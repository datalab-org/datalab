<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="row mb-3 align-items-center">
      <div class="col">
        <FileSelectDropdown
          v-model="file_id"
          :item_id="item_id"
          :block_id="block_id"
          :extensions="blockInfo.attributes.accepted_file_extensions"
          update-block-on-change
        />
      </div>
    </div>

    <div v-if="file_id">
      <div class="row mb-3 align-items-center">
        <div class="col-auto">
          <label class="form-label me-2 mb-0"><b>Cycles to plot:</b></label>
        </div>
        <div class="col-auto">
          <input
            id="cycles-input"
            v-model="cyclesString"
            type="text"
            class="form-control w-100"
            style="min-width: 14rem"
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
        </div>
        <div class="col-auto">
          <span id="list-of-cycles" class="ms-2">Showing cycles: {{ parsedCycles }}</span>
        </div>
      </div>

      <div v-if="cycle_num_error" class="alert alert-danger mb-3 mx-auto">
        {{ cycle_num_error }}
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-auto">
          <label class="form-label me-2 mb-0"><b>Mode:</b></label>
        </div>
        <div class="col">
          <div class="btn-group" role="group" aria-label="Mode selection">
            <button
              type="button"
              class="btn btn-outline-secondary"
              :class="{ active: derivative_mode == 'final capacity' }"
              @click="
                derivative_mode = derivative_mode == 'final capacity' ? null : 'final capacity';
                updateBlock();
              "
            >
              Cycle Summary
            </button>
            <button
              type="button"
              class="btn btn-outline-secondary"
              :class="{ active: derivative_mode == 'dQ/dV' }"
              @click="
                derivative_mode = derivative_mode == 'dQ/dV' ? null : 'dQ/dV';
                updateBlock();
              "
            >
              d<i>Q</i>/d<i>V</i>
            </button>
            <button
              type="button"
              class="btn btn-outline-secondary"
              :class="{ active: derivative_mode == 'dV/dQ' }"
              @click="
                derivative_mode = derivative_mode == 'dV/dQ' ? null : 'dV/dQ';
                updateBlock();
              "
            >
              d<i>V</i>/d<i>Q</i>
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="derivative_mode == 'dQ/dV' || derivative_mode == 'dV/dQ'"
        v-show="derivative_mode"
        class="row mb-3 align-items-center"
      >
        <div class="col-md-4 slider">
          <input
            id="s_spline"
            v-model="s_spline"
            type="range"
            class="form-range"
            name="s_spline"
            min="1"
            max="10"
            step="0.2"
            @change="isReplotButtonDisplayed = true"
          />
          <label
            for="s_spline"
            class="form-label mb-0"
            @mouseover="showDescription1 = true"
            @mouseleave="showDescription1 = false"
          >
            <span>Spline fit:</span> {{ -s_spline }}
          </label>
        </div>
        <div class="col-md-4 slider">
          <input
            id="win_size_1"
            v-model="win_size_1"
            type="range"
            class="form-range"
            name="win_size_1"
            min="501"
            max="1501"
            @change="isReplotButtonDisplayed = true"
          />
          <label
            for="win_size_1"
            class="form-label mb-0"
            @mouseover="showDescription2 = true"
            @mouseleave="showDescription2 = false"
          >
            <span>Window Size 1:</span> {{ win_size_1 }}
          </label>
        </div>
        <div class="col-md-4 d-flex align-items-center">
          <button
            v-show="isReplotButtonDisplayed"
            class="btn btn-sm btn-secondary"
            @click="updateBlock"
          >
            Recalculate
          </button>
        </div>
      </div>

      <div v-show="showDescription1" class="alert alert-info mb-3">
        <p class="mb-0">
          Smoothing parameter that determines how close the spline fits to the real data. Larger
          values result in a smoother fit with decreased detail.
        </p>
      </div>
      <div v-show="showDescription2" class="alert alert-info mb-3">
        <p class="mb-0">Window size for the Savitzky-Golay filter to apply to the derivatives.</p>
      </div>

      <div class="row mt-4">
        <div
          class="col mx-auto"
          :class="{ 'limited-width': bokehPlotLimitedWidth, blurry: isUpdating }"
        >
          <BokehPlot :bokeh-plot-data="bokehPlotData" />
        </div>
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { updateBlockFromServer } from "@/server_fetch_utils.js";
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
  data() {
    return {
      cycle_num_error: "",
      cyclesString: "",
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,
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
    // normalizingMass() {
    //   return this.$store.all_item_data[this.item_id]["characteristic_mass"] || null;
    // },
    file_id: createComputedSetterForBlockField("file_id"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
    characteristic_mass: createComputedSetterForBlockField("characteristic_mass"),
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

.btn-default:hover {
  background-color: #eee;
}

.slider span {
  border-bottom: 2px dotted #0c5460;
  text-decoration: none;
}
</style>
