<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="form-row mb-2">
      <div class="btn-group" role="group" aria-label="File selection mode">
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === 'single' }"
          @click="mode = 'single'"
        >
          Single File
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: mode === 'multi' }"
          @click="mode = 'multi'"
        >
          Multi File Stitch
        </button>
      </div>
    </div>
    <div class="form-row mb-2">
      <component
        :is="mode === 'multi' ? 'FileMultiSelectDropdown' : 'FileSelectDropdown'"
        v-model="fileModel"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        :update-block-on-change="false"
        @update:modelValue="onFileSelectionChange"
      />
    </div>
    <div class="form-row mt-2">
      <button class="btn btn-primary btn-sm" @click="applyFileSelection">Apply Selection</button>
    </div>
    <CollapsibleComparisonFileSelect
      v-model="comparisonFileModel"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      :exclude-file-ids="file_ids"
      :initially-expanded="comparisonFileModel.length > 0"
      @apply="applyComparisonFiles"
    />
    <div>
      <div class="form-row">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Cycles to plot:</b></label>
          <input
            id="cycles-input"
            v-model="cyclesString"
            type="text"
            class="form-control"
            placeholder="e.g., 1-5, 7, 9-10. Starts at 1."
            :class="{ 'is-invalid': cycle_num_error }"
            @keydown.enter="
              parseCycleString();
              updateBlock();
            "
            @blur="
              parseCycleString();
              updateBlock();
            "
          />
          <span id="list-of-cycles" class="pl-3 pt-2">Showing cycles: {{ parsedCycles }}</span>
        </div>

        <div v-if="cycle_num_error" class="alert alert-danger mt-2 mx-auto">
          {{ cycle_num_error }}
        </div>
      </div>

      <div class="form-row mt-2">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Mode:</b></label>
          <div class="btn-group">
            <div
              class="btn btn-default"
              :class="{ active: derivative_mode == 'final capacity' }"
              @click="
                derivative_mode = derivative_mode == 'final capacity' ? null : 'final capacity';
                updateBlock();
              "
            >
              Cycle Summary
            </div>
            <div
              class="btn btn-default"
              :class="{ active: derivative_mode == 'dQ/dV' }"
              @click="
                derivative_mode = derivative_mode == 'dQ/dV' ? null : 'dQ/dV';
                updateBlock();
              "
            >
              d<i>Q</i>/d<i>V</i>
            </div>
            <div
              class="btn btn-default"
              :class="{ active: derivative_mode == 'dV/dQ' }"
              @click="
                derivative_mode = derivative_mode == 'dV/dQ' ? null : 'dV/dQ';
                updateBlock();
              "
            >
              d<i>V</i>/d<i>Q</i>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="derivative_mode == 'dQ/dV' || derivative_mode == 'dV/dQ'"
        v-show="derivative_mode"
        class="row"
      >
        <div class="col-md slider" style="max-width: 250px">
          <input
            id="s_spline"
            v-model="s_spline"
            type="range"
            class="form-control-range"
            name="s_spline"
            min="1"
            max="10"
            step="0.2"
            @change="isReplotButtonDisplayed = true"
          />
          <label
            for="s_spline"
            @mouseover="showDescription1 = true"
            @mouseleave="showDescription1 = false"
          >
            <span>Spline fit:</span> {{ -s_spline }}
          </label>
        </div>
        <div class="col-md slider" style="max-width: 250px">
          <input
            id="win_size_1"
            v-model="win_size_1"
            type="range"
            class="form-control-range"
            name="win_size_1"
            min="501"
            max="1501"
            @change="isReplotButtonDisplayed = true"
          />
          <label
            for="win_size_1"
            @mouseover="showDescription2 = true"
            @mouseleave="showDescription2 = false"
          >
            <span>Window Size 1:</span> {{ win_size_1 }}
          </label>
        </div>
        <button v-show="isReplotButtonDisplayed" class="btn btn-default my-4" @click="updateBlock">
          Recalculate
        </button>
      </div>

      <div v-show="showDescription1" class="alert alert-info">
        <p>
          Smoothing parameter that determines how close the spline fits to the real data. Larger
          values result in a smoother fit with decreased detail.
        </p>
      </div>
      <div v-show="showDescription2" class="alert alert-info">
        <p>Window size for the Savitzky-Golay filter to apply to the derivatives.</p>
      </div>

      <div class="row mt-2">
        <div
          class="col mx-auto"
          :class="{ 'limited-width': bokehPlotLimitedWidth, blurry: isUpdating }"
        >
          <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
        </div>
      </div>
    </div>
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
  data() {
    return {
      cycle_num_error: "",
      cyclesString: "",
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,
      pending_file_ids: [],
      pending_single_file_id: null,
      pending_comparison_file_ids: [],
      single_mode_file: null,
      multi_mode_files: [],
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
        if (this.mode === "multi") {
          return this.pending_file_ids;
        } else {
          return this.pending_single_file_id;
        }
      },
      set(val) {
        if (this.mode === "multi") {
          this.pending_file_ids = Array.isArray(val) ? val : [val];
        } else {
          this.pending_single_file_id = val;
        }
      },
    },
    comparisonFileModel: {
      get() {
        return this.pending_comparison_file_ids;
      },
      set(val) {
        this.pending_comparison_file_ids = Array.isArray(val) ? val : [val];
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
    mode: createComputedSetterForBlockField("mode"),
    comparison_file_ids: createComputedSetterForBlockField("comparison_file_ids"),
  },
  watch: {
    mode(newMode, oldMode) {
      if (oldMode === "single" && newMode === "multi") {
        // Save current single mode selection
        this.single_mode_file = this.pending_single_file_id;
        // Restore multi mode selection
        this.pending_file_ids = this.multi_mode_files.slice();
      } else if (oldMode === "multi" && newMode === "single") {
        // Save current multi mode selection
        this.multi_mode_files = this.pending_file_ids.slice();
        // Restore single mode selection
        this.pending_single_file_id = this.single_mode_file;
      }
    },
  },
  mounted() {
    // Set default mode to 'single' if not already set
    if (!this.mode) {
      this.mode = "single";
    }

    // Ensure file_ids is always an array
    if (!Array.isArray(this.file_ids)) {
      this.file_ids = [];
      console.log("file_ids was not an array, so it has been reset to an empty array.");
    }

    // Initialize mode-specific selections from persisted file_ids
    if (this.mode === "multi") {
      // Multi mode: restore the file list from persisted file_ids
      this.pending_file_ids = this.file_ids.slice();
      this.multi_mode_files = this.file_ids.slice();
    } else {
      // Single mode: restore the single file from persisted file_ids
      this.pending_single_file_id = this.file_ids.length > 0 ? this.file_ids[0] : null;
      this.single_mode_file = this.pending_single_file_id;
    }

    // Initialize pending comparison files from persisted state
    if (this.comparison_file_ids && Array.isArray(this.comparison_file_ids)) {
      this.pending_comparison_file_ids = this.comparison_file_ids.slice();
    }
  },
  methods: {
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
    onFileSelectionChange() {
      // Auto-update in single mode when file selection changes
      if (this.mode === "single") {
        this.file_ids = this.pending_single_file_id ? [this.pending_single_file_id] : [];
        this.single_mode_file = this.pending_single_file_id;
        this.updateBlock();
      }
      // In multi mode, just stage the selection (don't auto-update)
    },
    applyFileSelection() {
      if (this.mode === "multi") {
        this.file_ids = this.pending_file_ids.slice();
        this.multi_mode_files = this.pending_file_ids.slice();
      } else {
        this.file_ids = this.pending_single_file_id ? [this.pending_single_file_id] : [];
        this.single_mode_file = this.pending_single_file_id;
      }
      this.updateBlock();
    },
    applyComparisonFiles() {
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
  max-width: 650px;
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
