<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="form-row col-lg-8">
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="['.mpr', '.txt', '.xls', '.xlsx', '.txt', '.res']"
        updateBlockOnChange
      />
    </div>
    <div class="form-row col-md-6 col-lg-7 mt-2">
      <div class="input-group form-inline">
        <label class="mr-2"><b>Cycles to plot:</b></label>
        <input
          type="text"
          class="form-control"
          :class="{ 'is-invalid': cycle_num_error }"
          v-model="cyclesString"
          @keydown.enter="
            parseCycleString();
            updateBlock();
          "
          @blur="
            parseCycleString();
            updateBlock();
          "
        />
        <label id="listOfCycles" class="ml-3">Showing cycles: {{ parsedCycles }}</label>
      </div>

      <div v-if="cycle_num_error" class="alert alert-danger mt-2 mx-auto">
        {{ cycle_num_error }}
      </div>
    </div>

    <div class="form-row">
      <div class="col mt-2">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Derivative mode:</b></label>
          <div class="btn-group">
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
    </div>

    <div v-show="derivative_mode" class="row">
      <div class="col-md slider" style="max-width: 250px">
        <input
          type="range"
          class="form-control-range"
          v-model="s_spline"
          id="s_spline"
          name="s_spline"
          min="1"
          max="10"
          step="0.2"
          @change="isReplotButtonDisplayed = true"
        />
        <label
          @mouseover="showDescription1 = true"
          @mouseleave="showDescription1 = false"
          for="s_spline"
        >
          <span>Spline fit:</span> {{ -s_spline }}
        </label>
      </div>
      <div class="col-md slider" style="max-width: 250px">
        <input
          type="range"
          class="form-control-range"
          v-model="win_size_1"
          id="win_size_1"
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

    <div class="alert alert-info" v-show="showDescription1">
      <p>
        Smoothing parameter that determines how close the spline fits to the real data. Larger
        values result in a smoother fit with decreased detail.
      </p>
    </div>
    <div class="alert alert-info" v-show="showDescription2">
      <p>Window size for the Savitzky-Golay filter to apply to the derivatives.</p>
    </div>

    <div class="row mt-2">
      <div
        class="col mx-auto"
        :class="{ 'limited-width': bokehPlotLimitedWidth, blurry: isUpdating }"
      >
        <BokehPlot :bokehPlotData="bokehPlotData" />
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
  props: {
    item_id: String,
    block_id: String,
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
    file_id: createComputedSetterForBlockField("file_id"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
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
          all_cycles.push(parseInt(split_section[0]));
        } else {
          let upper_range = parseInt(split_section[1]);
          let lower_range = parseInt(split_section[0]);
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
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
      ).then(() => {
        this.bokehPlotLimitedWidth = this.derivative_mode != "dQ/dV";
        this.isReplotButtonDisplayed = false;
      });
    },
  },
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
  },
};
</script>

<style scoped>
#listOfCycles {
  color: grey;
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
