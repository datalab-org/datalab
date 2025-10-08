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
        :update-block-on-change="mode !== 'multi'"
      />
    </div>
    <div v-if="mode === 'multi'" class="form-row mt-2">
      <button class="btn btn-primary btn-sm" @click="applyMultiSelect">Apply Selection</button>
    </div>
    <div class="comparison-header collapsible" :class="{ expanded: comparisonEnabled }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        @click="toggleComparison"
      />
      <span class="comparison-title" @click="toggleComparison">Comparison Files</span>
    </div>
    <div
      ref="comparisonContainer"
      class="comparison-content-container"
      :style="{ 'max-height': comparisonMaxHeight }"
    >
      <div class="form-row align-items-center mb-2">
        <FileMultiSelectDropdown
          v-model="comparisonFileModel"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
          :update-block-on-change="false"
          :exclude-file-ids="file_ids"
        />
      </div>
      <div class="form-row mt-2 mb-3">
        <button class="btn btn-primary btn-sm" @click="applyComparisonFiles">
          Apply Comparison Files
        </button>
      </div>
    </div>
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

import { updateBlockFromServer } from "@/server_fetch_utils.js";
import { createComputedSetterForBlockField } from "@/field_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    FileMultiSelectDropdown,
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
      cycle_num_error: "",
      cyclesString: "",
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,
      pending_file_ids: [],
      pending_comparison_file_ids: [],
      comparisonMaxHeight: "0px",
      padding_height: 18,
      comparisonEnabled: false,
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
        const ids = this.file_ids || [];
        if (this.mode === "multi") {
          return this.pending_file_ids;
        } else {
          return ids[0] || null;
        }
      },
      set(val) {
        if (this.mode === "multi") {
          this.pending_file_ids = Array.isArray(val) ? val : [val];
        } else {
          this.file_ids = val ? [val] : [];
          this.updateBlock();
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
  mounted() {
    // Ensure file_ids is always an array
    if (!Array.isArray(this.file_ids)) {
      this.file_ids = [];
      console.log("file_ids was not an array, so it has been reset to an empty array.");
    }
    if (this.mode === "multi") {
      // Ensure pending_file_ids matches persisted file_ids on reload
      this.pending_file_ids = this.file_ids.slice();
    }
    // Initialize pending comparison files from persisted state
    if (this.comparison_file_ids && Array.isArray(this.comparison_file_ids)) {
      this.pending_comparison_file_ids = this.comparison_file_ids.slice();
      // Auto-expand if there are comparison files
      this.comparisonEnabled = this.comparison_file_ids.length > 0;
    }

    // Initialize comparison section collapse state
    var comparisonContent = this.$refs.comparisonContainer;
    if (comparisonContent) {
      if (this.comparisonEnabled) {
        this.comparisonMaxHeight = "none";
        comparisonContent.style.overflow = "visible";
      } else {
        this.comparisonMaxHeight = "0px";
      }

      comparisonContent.addEventListener("transitionend", () => {
        if (this.comparisonEnabled) {
          this.comparisonMaxHeight = "none";
        }
      });
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
    applyMultiSelect() {
      if (this.mode !== "multi") return;
      this.file_ids = this.pending_file_ids.slice();
      this.updateBlock();
    },
    applyComparisonFiles() {
      this.comparison_file_ids = this.pending_comparison_file_ids.slice();
      this.updateBlock();
    },
    toggleComparison() {
      var content = this.$refs.comparisonContainer;
      if (!this.comparisonEnabled) {
        this.comparisonMaxHeight = content.scrollHeight + 2 * this.padding_height + "px";
        this.comparisonEnabled = true;
        content.style.overflow = "visible";
      } else {
        content.style.overflow = "hidden";
        requestAnimationFrame(() => {
          this.comparisonMaxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.comparisonMaxHeight = "0px";
            this.comparisonEnabled = false;
          });
        });
      }
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

.comparison-header {
  display: flex;
  align-items: center;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.comparison-title {
  margin-left: 0.5em;
  font-size: 1rem;
  font-weight: 500;
  color: #004175;
}

.collapse-arrow {
  color: #004175;
  transition: all 0.4s;
  cursor: pointer;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.expanded .collapse-arrow {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

.comparison-content-container {
  overflow: hidden;
  max-height: none;
  transition: max-height 0.4s ease-in-out;
}
</style>
