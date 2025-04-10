<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="mb-3">
      <label for="sampleDropdown" class="form-label">Select a sample file:</label>
      <FileSelectDropdown
        id="sampleDropdown"
        v-model="sample_file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        update-block-on-change
      />
    </div>

    <div class="mb-3">
      <label for="referenceDropdown" class="form-label">Select a reference file:</label>
      <FileSelectDropdown
        id="referenceDropdown"
        v-model="reference_file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        update-block-on-change
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
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    sample_file_id: createComputedSetterForBlockField("sample_file_id"),
    reference_file_id: createComputedSetterForBlockField("reference_file_id"),
    blockInfo() {
      return this.$store.state.blocksInfos["uvvis"];
    },
  },

  methods: {
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
  },
};
</script>

<style scoped></style>
