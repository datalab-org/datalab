<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="form-row">
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        update-block-on-change
      />
    </div>

    <div v-if="file_id">
      <div class="row">
        <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
          <BokehPlot :bokeh-plot-data="bokehPlotData" />
        </div>
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    block_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      massParseError: "",
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["buba"];
    },
    sorbent_mass_g: createComputedSetterForBlockField("sorbent_mass_g"),
    file_id: createComputedSetterForBlockField("file_id"),
  },
  mounted() {
    document.addEventListener("bokehStateUpdate", this.handleBokehStateUpdate);
  },
  beforeUnmount() {
    document.removeEventListener("bokehStateUpdate", this.handleBokehStateUpdate);
  },
  methods: {
    parseMass() {
      if (isNaN(this.sorbent_mass_g) || isNaN(parseFloat(this.sorbent_mass_g))) {
        this.massParseError = "Please provide a valid number";
      } else {
        this.massParseError = "";
      }
    },
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
    handleBokehStateUpdate(event) {
      console.log("handlingBokehStateUpdate", event.detail);
      // Now you can access this.item_id, this.block_id, etc.
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
        event.detail,
      );
    },
  },
};
</script>
