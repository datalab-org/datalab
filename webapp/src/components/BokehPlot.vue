<template>
  <!-- <div v-if="!loaded" class="alert alert-secondary mt-3">Data will be displayed here</div> -->
  <div v-if="loading" class="alert alert-secondary mt-3">Setting up bokeh plot...</div>
  <div :id="unique_id" ref="bokehPlotContainer" :style="{ height: bokehPlotContainerHeight }" />
</template>

<script>
import * as Bokeh from "@bokeh/bokehjs";
// var BokehDoc = null

export default {
  props: {
    bokehPlotData: {
      type: Object,
      required: true,
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
    this.$nextTick(() => {
      this.startBokehPlot();
    });
  },
  unmounted() {
    this.cleanupBokehPlot();
  },
  // BokehDoc: null, // this is a non-reactive property. We don't put this is in Data so Vue doesn't wrap it in a Proxy, which breaks its document.clear() functionality (for some reason)
  methods: {
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
            element.classList.add("form-control", "ml-4");
            element.classList.remove("bk-input", "bk");
          });
          var bokehSelectLabelElements = document.querySelectorAll("div.bk-input-group>label");
          bokehSelectLabelElements.forEach((element) => {
            element.classList.remove("bk");
          });
          var bokehInputGroups = document.querySelectorAll("div.bk-input-group");
          bokehInputGroups.forEach((element) => {
            element.classList.add("input-group", "form-inline", "col-sm-6");
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
