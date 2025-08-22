<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div>
      <MultiFileSelector
        v-model="selectedFileOrder"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="accepted_file_extensions"
        :main-label="'Select and order files: First file should be the reference scan, the subsequent files will be the sample scans.'"
        :update-block-on-change="true"
      />
    </div>
    <div class="row">
      <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData" />
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import MultiFileSelector from "@/components/FileMultiSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";

export default {
  components: {
    DataBlockBase,
    BokehPlot,
    MultiFileSelector,
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
      blockType: "uv-vis",
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos[this.blockType];
    },
    accepted_file_extensions() {
      return this.blockInfo?.attributes?.accepted_file_extensions || [];
    },
    selectedFileOrder: createComputedSetterForBlockField("selected_file_order"),
  },
};
</script>

<style scoped></style>
