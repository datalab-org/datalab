<template>
  <DataBlockBase ref="xrdBlockBase" :item_id="item_id" :block_id="block_id">
    <template #controls>
      <div class="form-row align-items-center mb-2">
        <button class="btn btn-outline-secondary mr-3" type="button" @click="toggleMultiSelect">
          {{ isMultiSelect ? "Switch to Single File" : "Switch to Multi-File" }}
        </button>
        <component
          :is="isMultiSelect ? 'FileMultiSelectDropdown' : 'FileSelectDropdown'"
          v-model="fileModel"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
          :default-to-all-files="!isMultiSelect"
          :update-block-on-change="!isMultiSelect"
        />
      </div>
      <div v-if="isMultiSelect" class="form-row mt-2">
        <button class="btn btn-primary btn-sm" @click="applyMultiSelect">Apply Selection</button>
      </div>
    </template>

    <template #plot>
      <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
    </template>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import FileMultiSelectDropdown from "@/components/FileMultiSelectDropdown";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    FileMultiSelectDropdown,
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
      pending_file_ids: [],
    };
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
    file_id: createComputedSetterForBlockField("file_id"),
    file_ids: createComputedSetterForBlockField("file_ids"),
    isMultiSelect: createComputedSetterForBlockField("isMultiSelect"),
    prev_file_ids: createComputedSetterForBlockField("prev_file_ids"),
    prev_single_file_id: createComputedSetterForBlockField("prev_single_file_id"),
    fileModel: {
      get() {
        const ids = this.file_ids || [];
        if (this.isMultiSelect) {
          return this.pending_file_ids;
        } else {
          return ids[0] || this.file_id || null;
        }
      },
      set(val) {
        if (this.isMultiSelect) {
          this.pending_file_ids = Array.isArray(val) ? val : [val];
        } else {
          this.file_ids = val ? [val] : [];
          this.file_id = val || null;
          this.updateBlock();
        }
      },
    },
  },

  mounted() {
    if (!Array.isArray(this.file_ids)) {
      this.file_ids = [];
    }
    if (this.isMultiSelect) {
      this.pending_file_ids = this.file_ids.slice();
    }
  },

  methods: {
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
    toggleMultiSelect() {
      if (this.isMultiSelect) {
        this.prev_file_ids = this.file_ids.slice();
        if (this.prev_single_file_id) {
          this.file_ids = [this.prev_single_file_id];
          this.file_id = this.prev_single_file_id;
        } else if (this.prev_file_ids.length > 0) {
          this.file_ids = [this.prev_file_ids[0]];
          this.file_id = this.prev_file_ids[0];
        } else {
          this.file_ids = [];
          this.file_id = null;
        }
      } else {
        this.prev_single_file_id = this.file_ids[0] || this.file_id || null;
        this.file_ids =
          this.prev_file_ids && this.prev_file_ids.length > 0 ? this.prev_file_ids.slice() : [];
        this.pending_file_ids = this.file_ids.slice();
        this.file_id = null;
      }
      this.isMultiSelect = !this.isMultiSelect;
      this.updateBlock();
    },
    applyMultiSelect() {
      if (!this.isMultiSelect) return;
      this.file_ids = this.pending_file_ids.slice();
      this.file_id = null;
      this.updateBlock();
    },
  },
};
</script>
