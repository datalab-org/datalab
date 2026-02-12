<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <template #controls>
      <div v-if="!isMultiSelect" class="form-inline mb-2">
        <FileSelectDropdown
          v-model="fileModel"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
        />
        <button class="btn btn-sm btn-primary ml-2" @click="toggleMultiSelect">
          Switch to multi-select
        </button>
      </div>

      <div v-else>
        <FileMultiSelectDropdown
          v-model="fileModel"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
          :main-label="'Select and order NMR files:'"
        />
        <div class="mt-2">
          <button
            class="btn btn-sm btn-primary"
            :disabled="!hasFileChanges"
            @click="applyMultiSelect"
          >
            Apply
          </button>
          <button class="btn btn-sm btn-secondary ml-2" @click="toggleMultiSelect">
            Switch to single-select
          </button>
        </div>
      </div>

      <div v-show="file_id || (file_ids && file_ids.length > 0)">
        <div class="form-inline mt-2">
          <div class="form-group">
            <label class="mr-2"><b>Process number:</b></label>
            <select v-model="selected_process" class="form-control" @change="updateBlock">
              <option v-for="process_number in block.available_processes" :key="process_number">
                {{ process_number }}
              </option>
            </select>
          </div>
        </div>

        <div class="mt-4">
          <span class="mr-2">
            <Isotope :isotope-string="metadata?.nucleus" /> {{ metadata?.pulse_program_name }}
          </span>
          <a type="button" class="btn btn-default btn-sm mb-2" @click="titleShown = !titleShown">{{
            titleShown ? "hide title" : "show title"
          }}</a>
        </div>
        <div v-if="titleShown" class="card mb-2">
          <div class="card-body" style="white-space: pre">
            {{ metadata?.topspin_title }}
          </div>
        </div>
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
import FileMultiSelectDropdown from "@/components/FileMultiSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import Isotope from "@/components/Isotope";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    FileMultiSelectDropdown,
    BokehPlot,
    Isotope,
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
      wavelengthParseError: "",
      titleShown: false,
      pending_file_ids: [],
    };
  },
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    metadata() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]?.metadata;
    },
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["nmr"];
    },
    file_id: createComputedSetterForBlockField("file_id"),
    file_ids: createComputedSetterForBlockField("file_ids"),
    isMultiSelect: createComputedSetterForBlockField("isMultiSelect"),
    prev_file_ids: createComputedSetterForBlockField("prev_file_ids"),
    prev_single_file_id: createComputedSetterForBlockField("prev_single_file_id"),
    selected_process: createComputedSetterForBlockField("selected_process"),
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
    hasFileChanges() {
      if (!this.isMultiSelect) return false;
      const currentIds = this.file_ids || [];
      if (this.pending_file_ids.length !== currentIds.length) return true;
      return !this.pending_file_ids.every((id, index) => id === currentIds[index]);
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

<style scoped>
.attribute-label {
  color: grey;
}

th {
  color: #454545;
  font-weight: 500;
}
</style>
