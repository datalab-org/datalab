<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-show="blockInfo.attributes.accepted_file_extensions.length > 0"
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      update-block-on-change
    />
    <div v-if="file_id && blockInfo">
      <div v-if="haveWavelengthProperties">
        <div class="form-row col-md-6 col-lg-4 mt-2 mb-2 pl-0">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ properties.wavelength.label }}</b></label
            >
            <input
              v-model="wavelength"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': wavelengthParseError }"
              @keydown.enter="
                parseWavelength();
                updateBlock();
              "
              @blur="
                parseWavelength();
                updateBlock();
              "
            />
            <div v-if="wavelengthParseError" class="alert alert-danger mt-2 mx-auto">
              {{ wavelengthParseError }}
            </div>
          </div>
        </div>
      </div>
      <div v-if="haveCycleProperties">
        <div class="form-row">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ properties.cycle.label }}</b></label
            >
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
          <button
            v-show="isReplotButtonDisplayed"
            class="btn btn-default my-4"
            @click="updateBlock"
          >
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
      </div>
      <div v-if="haveBokehPlot">
        <div class="row">
          <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
            <BokehPlot :bokeh-plot-data="bokehPlotData" />
          </div>
        </div>
      </div>
      <img
        v-if="isPhoto"
        data-testid="media-block-img"
        :src="media_url"
        class="img-fluid mx-auto"
      />
      <video v-if="isVideo" :src="media_url" controls class="mx-auto" />
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { blockTypes, API_URL } from "@/resources.js";
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
  data() {
    return {
      // Wavelength: XRD
      wavelengthParseError: "",
      // Cycle: Cycle
      cycle_num_error: "",
      cyclesString: "",
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,
    };
  },
  computed: {
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    block_data() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockInfo() {
      return this.block_data?.blocktype
        ? this.$store.state.blocksInfos[this.block_data.blocktype]
        : null;
    },
    properties() {
      return this.block_data?.blocktype ? blockTypes[this.block_data.blocktype]?.properties : null;
    },
    bokehPlotData() {
      if (!this.file_id) return null;
      return (
        this.$store.state.all_item_data[this.item_id]?.["blocks_obj"]?.[this.block_id]
          ?.bokeh_plot_data || null
      );
    },
    haveBokehPlot() {
      return this.properties && "bokehPlot" in this.properties;
    },
    haveWavelengthProperties() {
      return this.properties && "wavelength" in this.properties;
    },
    media_url() {
      // If the API has already base64 encoded the image, then use it,
      let b64_encoding = this.block_data["b64_encoded_image"] || null;
      if ((b64_encoding != null && b64_encoding[this.file_id]) || null != null) {
        return `data:image/png;base64,${b64_encoding[this.file_id]}`;
      }
      return `${API_URL}/files/${this.file_id}/${this.lookup_file_field("name", this.file_id)}`;
    },
    isPhoto() {
      return [".png", ".jpeg", ".jpg", ".tif", ".tiff"].includes(
        this.lookup_file_field("extension", this.file_id),
      );
    },
    isVideo() {
      return [".mp4", ".mov", ".webm"].includes(this.lookup_file_field("extension", this.file_id));
    },
    haveCycleProperties() {
      return this.properties && "cycle" in this.properties;
    },
    numberOfCycles() {
      return (
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
          .number_of_cycles || null
      );
    },
    parsedCycles() {
      return this.all_cycles ? this.all_cycles : "all";
    },
    file_id: createComputedSetterForBlockField("file_id"),
    wavelength: createComputedSetterForBlockField("wavelength"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
    characteristic_mass: createComputedSetterForBlockField("characteristic_mass"),
  },
  methods: {
    parseWavelength() {
      if (isNaN(this.wavelength) || isNaN(parseFloat(this.wavelength))) {
        this.wavelengthParseError = "Please provide a valid number";
      } else {
        this.wavelengthParseError = "";
      }
    },
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      ).then(() => {
        if (this.haveCycleProperties) {
          this.bokehPlotLimitedWidth = this.derivative_mode != "dQ/dV";
          this.isReplotButtonDisplayed = false;
        }
      });
    },
    lookup_file_field(field, file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.[field];
    },
  },
};
</script>

<style scoped>
image,
video {
  display: block;
  max-height: 600px;
}

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
