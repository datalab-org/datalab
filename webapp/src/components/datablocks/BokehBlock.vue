<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div v-if="multiFileBlock">
      <FileMultiSelect
        v-model="file_ids"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo?.attributes?.accepted_file_extensions"
        :main-label="'Select and order files'"
        update-block-on-change
      />
    </div>
    <div v-else>
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo?.attributes?.accepted_file_extensions"
        update-block-on-change
      />
    </div>

    <div id="bokehPlotContainer" class="limited-width">
      <BokehPlot :bokeh-plot-data="bokehPlotData" />
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import FileMultiSelect from "@/components/FileMultiSelect";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    FileMultiSelect,
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
    multiFileBlock() {
      if (this.blockInfo?.attributes?.multi_file) {
        return true;
      }
      return false;
    },
    blockInfo() {
      const blockType = this.blockType;
      if (!blockType) return null;
      return this.$store.state.blocksInfos[blockType] || null;
    },
    blockType() {
      try {
        return this.block["blocktype"];
      } catch {
        return null;
      }
    },
    file_id: createComputedSetterForBlockField("file_id"),
    file_ids: createComputedSetterForBlockField("file_ids"),
  },

  methods: {
    updateBlock() {
      updateBlockFromServer(this.item_id, this.block_id, this.block).catch((error) => {
        console.error("Error updating block:", error);
      });
    },
  },
};
</script>

<style scoped>
.limited-width {
  max-width: 100%;
}
</style>
