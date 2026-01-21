<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
  <template #controls>

    <div class="form-row mb-2">
      <div class="btn-group" role="group" aria-label="File selection mode">
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === FILE_MODE.SINGLE }"
          @click="mode = FILE_MODE.SINGLE"
        >
          Single File
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === FILE_MODE.MULTI }"
          @click="mode = FILE_MODE.MULTI"
        >
          Multi File Stitch
        </button>
      </div>
    </div>
    <div class="form-row mb-2">
      <component
        :is="mode === FILE_MODE.MULTI ? 'FileMultiSelectDropdown' : 'FileSelectDropdown'"
        v-model="fileModel"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        :update-block-on-change="false"
        @update:modelValue="onFileSelectionChange"
      />
    </div>
    <CollapsibleComparisonFileSelect
      v-model="pending_comparison_file_ids"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      :exclude-file-ids="file_ids"
      :initially-expanded="pending_comparison_file_ids.length > 0"
      :show-apply-button="false"
    />
    <div class="form-row mt-2">
        <button class="btn btn-primary btn-sm" @click="applyAllSelections">Apply Changes</button>
      </div>

      <div v-show="file_ids && file_ids.length > 0" class="mt-3">
        <div class="form-inline">
          <label class="mr-2"><b>Cycles to plot:</b></label>
          <input
            id="cycles-input"
            v-model="cyclesString"
            type="text"
            class="form-control"
            placeholder="e.g., 1-5, 7, 9-10. Starts at 1."
            :class="{ 'is-invalid': cycle_num_error }"
            @keydown.enter="parseCycleString(); updateBlock();"
            @blur="parseCycleString(); updateBlock();"
          />
          <span id="list-of-cycles" class="pl-3 pt-2">Showing cycles: {{ parsedCycles }}</span>
          <a
            type="button"
            class="btn btn-default btn-sm ml-2"
            @click="showDescription1 = !showDescription1"
          >
            ?
          </a>
        </div>

        <div v-if="cycle_num_error" class="alert alert-danger mt-2">
          {{ cycle_num_error }}
        </div>

        <div class="form-inline mt-2">
          <label class="mr-2"><b>Smoothing parameter:</b></label>
          <input
            v-model="smoothing_factor"
            type="number"
            class="form-control"
            min="0"
            step="0.01"
          />
          <a
            type="button"
            class="btn btn-default btn-sm ml-2"
            @click="showDescription2 = !showDescription2"
          >
            ?
          </a>
        </div>

        <div v-show="showDescription1" class="alert alert-info mt-2">
          <p>
            Specify which cycles to plot. Use commas to separate individual cycles and hyphens for
            ranges. Leave empty or type 'all' to plot all cycles.
          </p>
        </div>
        <div v-show="showDescription2" class="alert alert-info mt-2">
          <p>
            Smoothing parameter for the Savitzky-Golay filter applied to capacity vs voltage. Larger
            values result in a smoother fit with decreased detail.
          </p>
          <p>Window size for the Savitzky-Golay filter to apply to the derivatives.</p>
        </div>
      </div>
    </template>

    <template #plot>
      <div :class="{ blurry: isUpdating }">
        <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
      </div>
    </template>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import FileMultiSelectDropdown from "@/components/FileMultiSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import CollapsibleComparisonFileSelect from "@/components/CollapsibleComparisonFileSelect";

import { updateBlockFromServer } from "@/server_fetch_utils.js";
import { createComputedSetterForBlockField } from "@/field_utils.js";

// File selection mode constants
const FILE_MODE = {
  SINGLE: "single",
  MULTI: "multi",
};

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    FileMultiSelectDropdown,
    BokehPlot,
    CollapsibleComparisonFileSelect,
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
  // Expose constants to template for use in Vue 3
  setup() {
    return {
      FILE_MODE,
    };
  },
  data() {
    return {
      // Cycle input validation and display
      cycle_num_error: "",
      cyclesString: "",

      // UI state for tooltips and plot display
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,

      // File selection staging area (what user has selected but not yet applied)
      pending_file_ids: [], // Multi-mode: selected files before "Apply Selection"
      pending_single_file_id: null, // Single-mode: selected file before "Apply Selection"
      pending_comparison_file_ids: [], // Comparison files before "Apply Comparison Files"

      // Mode memory (preserves selections when switching modes - session-only, not persisted)
      single_mode_file: null, // Last file selected in single mode, restored when switching back
      multi_mode_files: [], // Last files selected in multi mode, restored when switching back
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    numberOfCycles() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .number_of_cycles;
    },
    parsedCycles() {
      return this.all_cycles ? this.all_cycles : "all";
    },
    isUpdating() {
      return this.$store.state.updating[this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos["cycle"];
    },
    fileModel: {
      get() {
        if (this.mode === FILE_MODE.MULTI) {
          return this.pending_file_ids;
        } else {
          return this.pending_single_file_id;
        }
      },
      set(val) {
        if (this.mode === FILE_MODE.MULTI) {
          this.pending_file_ids = Array.isArray(val) ? val : [val];
        } else {
          this.pending_single_file_id = val;
        }
      },
    },
    // normalizingMass() {
    //   return this.$store.all_item_data[this.item_id]["characteristic_mass"] || null;
    // },
    file_ids: createComputedSetterForBlockField("file_ids"),
    prev_file_ids: createComputedSetterForBlockField("prev_file_ids"),
    prev_single_file_id: createComputedSetterForBlockField("prev_single_file_id"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
    characteristic_mass: createComputedSetterForBlockField("characteristic_mass"),
    smoothing_factor: createComputedSetterForBlockField("s_spline"),
    mode: createComputedSetterForBlockField("mode"),
    comparison_file_ids: createComputedSetterForBlockField("comparison_file_ids"),
  },
  watch: {
    mode(newMode, oldMode) {
      this.handleModeSwitch(newMode, oldMode);
    },
  },
  mounted() {
    this.initializeMode();
    this.validateFileIds();
    this.initializeFileSelections();
    this.initializeComparisonFiles();
  },
  methods: {
    /**
     * Initialize mode to default if not set
     */
    initializeMode() {
      if (!this.mode) {
        this.mode = FILE_MODE.SINGLE;
      }
    },

    /**
     * Ensure file_ids is always an array
     */
    validateFileIds() {
      if (!Array.isArray(this.file_ids)) {
        this.file_ids = [];
        console.warn("file_ids was not an array, resetting to empty array.");
      }
    },

    /**
     * Initialize file selections based on current mode from persisted file_ids
     */
    initializeFileSelections() {
      if (this.mode === FILE_MODE.MULTI) {
        // Multi mode: restore the file list from persisted file_ids
        this.pending_file_ids = this.file_ids.slice();
        this.multi_mode_files = this.file_ids.slice();
      } else {
        // Single mode: restore the single file from persisted file_ids
        this.pending_single_file_id = this.file_ids.length > 0 ? this.file_ids[0] : null;
        this.single_mode_file = this.pending_single_file_id;
      }
    },

    /**
     * Initialize comparison files from persisted state
     */
    initializeComparisonFiles() {
      if (this.comparison_file_ids && Array.isArray(this.comparison_file_ids)) {
        this.pending_comparison_file_ids = this.comparison_file_ids.slice();
      }
    },

    /**
     * Handle switching between single and multi file modes
     * Saves current mode's selection and restores the target mode's previous selection
     */
    handleModeSwitch(newMode, oldMode) {
      if (oldMode === FILE_MODE.SINGLE && newMode === FILE_MODE.MULTI) {
        this.saveAndRestoreSelection(FILE_MODE.SINGLE);
      } else if (oldMode === FILE_MODE.MULTI && newMode === FILE_MODE.SINGLE) {
        this.saveAndRestoreSelection(FILE_MODE.MULTI);
      }
    },

    /**
     * Save the current mode's selection and restore the target mode's selection
     */
    saveAndRestoreSelection(fromMode) {
      if (fromMode === FILE_MODE.SINGLE) {
        // Save single mode selection
        this.single_mode_file = this.pending_single_file_id;
        // Restore multi mode selection
        this.pending_file_ids = this.multi_mode_files.slice();
      } else {
        // Save multi mode selection
        this.multi_mode_files = this.pending_file_ids.slice();
        // Restore single mode selection
        this.pending_single_file_id = this.single_mode_file;
      }
    },

    parseCycleString() {
      let cyclesString = this.cyclesString.replace(/\s/g, "");
      this.cycle_num_error = null;
      var cycle_regex = /^(\d+(-\d+)?,)*(\d+(-\d+)?)$/g;
      if (cyclesString.match(/^ *$/) !== null || cyclesString.toLowerCase() == "all") {
        this.all_cycles = null;
        return;
      } else if (!cycle_regex.test(cyclesString)) {
        this.cycle_num_error = `Invalid input '${cyclesString}', please enter comma-separated values or hyphen-separated ranges, e.g., '1, 2, 5-10'.`;
        return;
      }
      let cycle_string_sections = cyclesString.split(",");
      var all_cycles = [];
      for (const section of cycle_string_sections) {
        let split_section = section.split("-");
        if (split_section.length == 1) {
          let value = parseInt(split_section[0]);
          if (value < 1) {
            this.cycle_num_error = `Invalid input '${cyclesString}', cycle numbers start at 1.`;
            return;
          }
          all_cycles.push(parseInt(split_section[0]));
        } else {
          let upper_range = parseInt(split_section[1]);
          let lower_range = parseInt(split_section[0]);
          if (lower_range < 1) {
            this.cycle_num_error = `Invalid input '${cyclesString}', cycle numbers start at 1.`;
            return;
          }
          for (
            let j = Math.min(lower_range, upper_range);
            j <= Math.max(lower_range, upper_range);
            j++
          ) {
            all_cycles.push(j);
          }
        }
      }

      this.all_cycles = all_cycles;
    },
    /**
     * Update file_ids from pending selections based on current mode
     * Also updates mode memory to preserve selection when switching modes
     */
    updateFileIds() {
      if (this.mode === FILE_MODE.MULTI) {
        this.file_ids = this.pending_file_ids.slice();
        this.multi_mode_files = this.pending_file_ids.slice();
      } else {
        this.file_ids = this.pending_single_file_id ? [this.pending_single_file_id] : [];
        this.single_mode_file = this.pending_single_file_id;
      }
    },

    /**
     * Auto-update handler for file selection changes
     * In single mode: immediately applies the selection
     * In multi mode: only stages the selection (user must click "Apply Selection")
     */
    onFileSelectionChange() {
      if (this.mode === FILE_MODE.SINGLE) {
        this.updateFileIds();
        this.updateBlock();
      }
      // In multi mode, just stage the selection (don't auto-update)
    },

    /**
     * Apply all pending changes (file selection and comparison files)
     * Used by the consolidated "Apply Changes" button
     */
    applyAllSelections() {
      this.updateFileIds();
      this.comparison_file_ids = this.pending_comparison_file_ids.slice();
      this.updateBlock();
    },
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      ).then(() => {
        this.bokehPlotLimitedWidth = this.derivative_mode != "dQ/dV";
        this.isReplotButtonDisplayed = false;
      });
    },
  },
};
</script>

<style scoped>
#list-of-cycles {
  color: grey;
}

#cycles-input {
  max-width: 14em;
}

.blurry {
  filter: blur(5px);
}

.limited-width {
  max-width: 100%;
}

.slider {
  margin-top: 2rem;
}

.btn-default:hover {
  background-color: #eee;
}

.slider span {
  border-bottom: 2px dotted #0c5460;
  text-decoration: none;
}
</style>
