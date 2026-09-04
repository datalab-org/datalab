<template>
  <!-- <div v-if="!loaded" class="alert alert-secondary mt-3">Data will be displayed here</div> -->
  <div v-if="loading" class="alert alert-secondary mt-3">Setting up bokeh plot...</div>
  <div :id="unique_id" ref="bokehPlotContainer" :style="{ height: bokehPlotContainerHeight }" />
</template>

<script>
import * as Bokeh from "bokeh";

import store from "@/store/index.js";
import { getBlockData, updateBlockFromServer } from "@/server_fetch_utils.js";
// var BokehDoc = null

export default {
  props: {
    bokehPlotData: {
      type: Object,
      required: true,
    },
    // Widgets inside the plot dispatch `block-event` to ask the server for
    // something, and the event has to say which block it came from.
    item_id: {
      type: String,
      default: null,
    },
    block_id: {
      type: String,
      default: null,
    },
  },
  data: function () {
    return {
      unique_id: "dummy-bokeh-id",
      loading: false,
      loaded: false,
      bokeh_views: null,
      bokehPlotContainerHeight: "auto",
    };
  },
  watch: {
    bokehPlotData() {
      var scrollHeight = this.$refs.bokehPlotContainer.scrollHeight;
      this.bokehPlotContainerHeight = `${scrollHeight}px`;
      this.cleanupBokehPlot();
      this.startBokehPlot();
      window.requestAnimationFrame(() => {
        this.bokehPlotContainerHeight = "auto";
      });
      // this.bokehPlotContainerHeight = 'auto'
    },
  },
  mounted() {
    this.unique_id = this.guidGenerator();
    document.addEventListener("block-event", this.handleBokehEvent);
    this.$nextTick(() => {
      this.startBokehPlot();
    });
  },
  unmounted() {
    document.removeEventListener("block-event", this.handleBokehEvent);
    this.cleanupBokehPlot();
  },
  // BokehDoc: null, // this is a non-reactive property. We don't put this is in Data so Vue doesn't wrap it in a Proxy, which breaks its document.clear() functionality (for some reason)
  methods: {
    async handleBokehEvent(event) {
      // Only handle events for this specific block
      if (event.detail.block_id !== this.block_id) {
        return;
      }

      console.log("handlingBokehEvent", event.detail, "for block", this.block_id);

      // A request for data is a read, so it does not go anywhere near the block
      // update path: the arrays are patched into the plot that is already on
      // screen, which keeps its zoom, its selection and its widget state.
      if (event.detail.event_name === "get_data") {
        return this.patchColumns(event.detail);
      }

      updateBlockFromServer(
        this.item_id,
        this.block_id,
        store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
        event.detail,
      ).catch((error) => {
        console.error("Error updating block:", error);
      });
    },
    async patchColumns({ columns, source, keys }) {
      // `columns` says which columns to fetch and in what units; `keys` says what
      // to call each one in the data source. The plot decides both -- everything
      // here knows is how to put an array where it was asked to.
      const target = this.BokehDoc && this.BokehDoc.get_model_by_name(source);
      if (!target) {
        console.warn(`No data source named ${source} in this plot`);
        return;
      }

      try {
        const response = await getBlockData(this.item_id, this.block_id, columns);
        if (!response) {
          return;
        }

        const data = { ...target.data };
        for (const [column, values] of Object.entries(response.data)) {
          data[keys[column] ?? column] = values;
        }
        target.data = data;

        store.commit("setBlockError", { block_id: this.block_id, error: "" });
      } catch (error) {
        // The server explains refusals in terms the user can act on, e.g. which
        // metadata field a unit needs, so show it rather than only logging it.
        store.commit("setBlockError", {
          block_id: this.block_id,
          error: error?.message || String(error),
        });
      }
    },
    async startBokehPlot() {
      if (this.bokehPlotData) {
        this.cleanupBokehPlot();

        this.loading = true;
        console.log("running startBokehPlot with:");
        console.log(this.bokehPlotData);

        try {
          const targetElement = document.getElementById(this.unique_id);
          if (!targetElement) {
            console.warn(`Target element ${this.unique_id} not found, skipping Bokeh render`);
            this.loading = false;
            return;
          }

          var views = await Bokeh.embed.embed_item(this.bokehPlotData, this.unique_id);
          this.BokehDoc = views[0].model.document; // NOTE: BokehDoc is intentionally not kept in data so that this is NONREACTIVE. (we need this to be the case or BokehDoc.clear() doesn't work for some reason)
          this.bokeh_views = views;
          console.log("Bokeh Doc:");
          console.log(this.BokehDoc);
          this.loading = false;
          this.loaded = true;

          // add some bootrap styles to bokeh widgets. This is not very elegants
          var bokehSelectElements = document.querySelectorAll("div.bk-input-group>select");
          bokehSelectElements.forEach((element) => {
            element.classList.add("form-control", "form-control-sm", "ml-2");
            element.classList.remove("bk-input", "bk");
          });
          var bokehSelectLabelElements = document.querySelectorAll("div.bk-input-group>label");
          bokehSelectLabelElements.forEach((element) => {
            element.classList.remove("bk");
          });
          var bokehInputGroups = document.querySelectorAll("div.bk-input-group");
          bokehInputGroups.forEach((element) => {
            // No width class here: a widget's width is set by whatever the plot put
            // it in. Pinning every input group to half a row overrode that, so a
            // control laid out to fill its column only ever filled half of it.
            element.classList.add("input-group", "form-inline");
            element.classList.remove("bk-input-group", "bk");
          });
        } catch (error) {
          console.error("Error starting Bokeh plot:", error);
          this.loading = false;
        }
      }
    },
    cleanupBokehPlot() {
      if (this.BokehDoc) {
        console.log("cleaning up bokeh plot");
        try {
          this.BokehDoc.clear();
          const i = Bokeh.documents.indexOf(this.BokehDoc);
          if (i > -1) {
            Bokeh.documents.splice(i, 1);
          }
        } catch (error) {
          console.warn("Error during Bokeh cleanup:", error);
        }
        this.BokehDoc = null;
      }

      if (this.bokeh_views) {
        try {
          this.bokeh_views.forEach((view) => {
            if (view && view.remove) {
              view.remove();
            }
          });
        } catch (error) {
          console.warn("Error cleaning up Bokeh views:", error);
        }
        this.bokeh_views = null;
      }
    },
    guidGenerator() {
      var S4 = function () {
        return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
      };
      return S4() + S4() + "-" + S4();
    },
  },
};
</script>
