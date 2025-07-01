<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase ref="xrdBlockBase" :item_id="item_id" :block_id="block_id">
    <div class="form-row">
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        :default-to-all-files="true"
        update-block-on-change
      />
    </div>

    <div id="bokehPlotContainer">
      <BokehPlot :bokeh-plot-data="bokehPlotData" />
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";

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
  computed: {
    bokehPlotData() {
      return this.block.bokeh_plot_data;
    },
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos["xrd"];
    },
    wavelength: createComputedSetterForBlockField("wavelength"),
    stagger_enabled: createComputedSetterForBlockField("stagger_enabled"),
    stagger_offset: createComputedSetterForBlockField("stagger_offset"),
    file_id: createComputedSetterForBlockField("file_id"),
  },
};
</script>
