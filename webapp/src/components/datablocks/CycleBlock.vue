<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <template #controls>
      <div v-if="!isMultiSelect" class="form-inline">
        <label class="mr-2"><b>Select file:</b></label>
        <FileSelectDropdown
          v-model="fileModel"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
          @change="handleFileChange"
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
          :main-label="'Select and order files:'"
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

      <div v-show="file_ids && file_ids.length > 0" class="mt-3">
        <div class="form-inline">
          <label class="mr-2"><b>Cycles to plot:</b></label>
          <input
            v-model="cyclesString"
            type="text"
            class="form-control"
            placeholder="e.g., 1,2,5-10 or 'all'"
            @input="isReplotButtonDisplayed = true"
          />
          <button
            class="btn btn-primary ml-2"
            :disabled="!isReplotButtonDisplayed"
            @click="updateBlock"
          >
            Replot
          </button>
          <a
            type="button"
            class="btn btn-default btn-sm ml-2"
            @click="showDescription1 = !showDescription1"
          >
            ?
          </a>
        </div>
        <div v-if="cycle_num_error" class="alert alert-danger mt-2">{{ cycle_num_error }}</div>

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
        if (this.isMultiSelect) {
          return this.pending_file_ids;
        } else {
          return ids[0] || null;
        }
      },
      set(val) {
        if (this.isMultiSelect) {
          this.pending_file_ids = Array.isArray(val) ? val : [val];
        } else {
          this.file_ids = val ? [val] : [];
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

    // normalizingMass() {
    //   return this.$store.all_item_data[this.item_id]["characteristic_mass"] || null;
    // },
    file_ids: createComputedSetterForBlockField("file_ids"),
    isMultiSelect: createComputedSetterForBlockField("isMultiSelect"),
    prev_file_ids: createComputedSetterForBlockField("prev_file_ids"),
    prev_single_file_id: createComputedSetterForBlockField("prev_single_file_id"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
    characteristic_mass: createComputedSetterForBlockField("characteristic_mass"),
    smoothing_factor: createComputedSetterForBlockField("s_spline"),
  },
  mounted() {
    // Ensure file_ids is always an array
    if (!Array.isArray(this.file_ids)) {
      this.file_ids = [];
      console.log("file_ids was not an array, so it has been reset to an empty array.");
    }
    if (this.isMultiSelect) {
      // Ensure pending_file_ids matches persisted file_ids on reload
      this.pending_file_ids = this.file_ids.slice();
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
    toggleMultiSelect() {
      if (this.isMultiSelect) {
        // Switching from multi to single: save multi selection, restore last single selection
        this.prev_file_ids = this.file_ids.slice();
        if (this.prev_single_file_id) {
          this.file_ids = [this.prev_single_file_id];
        } else if (this.prev_file_ids.length > 0) {
          this.file_ids = [this.prev_file_ids[0]];
        } else {
          this.file_ids = [];
        }
      } else {
        // Switching from single to multi: save single selection, restore previous multi selection or start empty
        this.prev_single_file_id = this.file_ids[0] || null;
        this.file_ids =
          this.prev_file_ids && this.prev_file_ids.length > 0 ? this.prev_file_ids.slice() : [];
        this.pending_file_ids = this.file_ids.slice();
      }
      this.isMultiSelect = !this.isMultiSelect;
      this.updateBlock();
    },
    // setMultiSelectFlag(flag) {
    //   // Store the flag in your block data for backend use
    //   this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].isMultiSelect =
    //     flag;
    // },
    applyMultiSelect() {
      if (!this.isMultiSelect) return;

      this.file_ids = this.pending_file_ids.slice();
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
