<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-if="blockInfo.attributes.accepted_file_extensions?.length > 0"
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
      <div v-if="haveProcessNumberProperties">
        <div class="form-inline mt-2">
          <div class="form-group">
            <label class="mr-2"
              ><b>{{ properties.processNumber.label }}</b></label
            >
            <select v-model="selected_process" class="form-control" @change="updateBlock">
              <option
                v-for="process_number in block_data.available_processes"
                :key="process_number"
              >
                {{ process_number }}
              </option>
            </select>
          </div>
        </div>

        <div class="mt-4">
          <span class="mr-2">
            <Isotope :isotope-string="block_data.nucleus" /> {{ block_data.pulse_program_name }}
          </span>
          <a type="button" class="btn btn-default btn-sm mb-2" @click="titleShown = !titleShown">{{
            titleShown ? "hide title" : "show title"
          }}</a>
          <a
            type="button"
            class="btn btn-default btn-sm mb-2 ml-2"
            @click="detailsShown = !detailsShown"
            >{{ detailsShown ? "hide measurement details" : "show measurement details" }}</a
          >
        </div>
        <div v-if="titleShown" class="card mb-2">
          <div class="card-body" style="white-space: pre">
            {{ block_data.topspin_title }}
          </div>
        </div>
      </div>
      <div v-if="haveBokehPlot">
        <div class="row">
          <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
            <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
            <div v-else class="alert alert-secondary">
              Plotting currently not available for data with dimension > 1
            </div>
          </div>
          <div v-if="detailsShown" class="col-xl-4 col-lg-4 ml-0">
            <table class="table table-sm">
              <tbody>
                <tr>
                  <th scope="row">nucleus</th>
                  <td><Isotope :isotope-string="block_data.nucleus" /></td>
                </tr>
                <tr>
                  <th scope="row">pulse program</th>
                  <td>{{ block_data.pulse_program_name }}</td>
                </tr>
                <tr>
                  <th scope="row">Data shape</th>
                  <td>
                    {{ block_data.processed_data_shape }} (<i>d</i> =
                    {{ block_data.processed_data_shape.length }})
                  </td>
                </tr>
                <tr>
                  <th scope="row">probe</th>
                  <td>{{ block_data.probe_name }} s</td>
                </tr>

                <tr>
                  <th scope="row"># of scans</th>
                  <td>{{ block_data.nscans }}</td>
                </tr>

                <tr>
                  <th scope="row">recycle delay</th>
                  <td>{{ block_data.recycle_delay }} s</td>
                </tr>
                <tr>
                  <th scope="row">carrier frequency</th>
                  <td>{{ block_data.carrier_frequency_MHz }} MHz</td>
                </tr>

                <tr>
                  <th scope="row">carrier offset</th>
                  <td>
                    {{
                      (block_data.carrier_offset_Hz / block_data.carrier_frequency_MHz).toFixed(1)
                    }}
                    ppm
                  </td>
                </tr>
                <tr>
                  <th scope="row">cnst31</th>
                  <td>{{ block_data.CNST31 }}</td>
                </tr>
              </tbody>
            </table>
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
    <div v-if="haveChatProperties">
      <div v-if="advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
        [show advanced]
      </div>
      <div v-if="!advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
        [hide advanced]
      </div>

      <div class="row">
        <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-12 mx-auto">
          <div v-if="!advancedHidden" class="advanced-information">
            <div class="input-group">
              <label class="mr-2">Model:</label>
              <select v-model="modelName" class="form-control">
                <option v-for="model in Object.keys(availableModels)" :key="model">
                  {{ model }}
                </option>
              </select>
            </div>
            <br />
            <div class="input-group">
              <label>Current conversation token count:</label>
              <span class="pl-1">{{ tokenCount }}/ {{ modelObj.context_window }}</span>
            </div>
            <div class="form-row input-group">
              <label>est. cost for next message:</label>
              <span class="pl-1">${{ estimatedCost.toPrecision(2) }}</span>
            </div>

            <div class="form-row input-group">
              <label for="temperatureInput" class="mr-2"><b>temperature:</b></label>
              <input
                id="temperatureInput"
                v-model="temperature"
                type="number"
                min="0"
                max="1"
                step="0.1"
                class="form-control-sm"
                :class="{ 'red-border': tempInvalid }"
              />
              <small v-show="tempInvalid" class="text-danger">
                Temperature must must be a number between 0 and 1
              </small>
            </div>
          </div>
          <ChatWindow
            :chat-messages="messages.slice(advancedHidden ? 2 : 0)"
            :is-loading="isLoading"
          />
          <div class="d-flex justify-content-center">
            <button
              class="btn btn-default btn-sm regenerate-button"
              :disabled="messages[messages.length - 1]['role'] != 'assistant'"
              @click="regenerateLastResponse"
            >
              <font-awesome-icon
                :icon="['fa', 'sync']"
                class="pr-1 text-muted"
                :spin="isRegenerating"
              />
              regenerate response
            </button>
          </div>
        </div>
      </div>
      <div v-if="errorMessage" style="white-space: pre-line" class="alert alert-warning">
        {{ errorMessage }}
      </div>
      <div v-show="estimatedCost > 0.1" class="alert alert-info col-lg-6 col-md-8 mt-3 mx-auto">
        <font-awesome-icon icon="exclamation-circle" /> sending a message is estimated to cost: ${{
          estimatedCost.toPrecision(2)
        }}
      </div>

      <div class="input-group form-inline col-md-10 mx-auto align-items-end">
        <textarea
          v-model="prompt"
          rows="3"
          type="text"
          class="form-control"
          :disabled="isLoading"
          placeholder="Type your message to send to the LLM, then press enter or hit send (shift-enter for newline)."
          @keydown.enter.exact.prevent="updateBlock"
        />
        <button
          type="button"
          class="btn btn-default send-button"
          :disabled="!prompt || /^\s*$/.test(prompt) || isLoading"
          @click="updateBlock()"
        >
          Send
        </button>
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import Isotope from "@/components/Isotope";
import ChatWindow from "@/components/ChatWindow";

import { blockTypes, API_URL } from "@/resources.js";
import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    Isotope,
    ChatWindow,
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
      // Wavelength
      wavelengthParseError: "",
      // Cycle
      cycle_num_error: "",
      cyclesString: "",
      showDescription1: false,
      showDescription2: false,
      bokehPlotLimitedWidth: true,
      isReplotButtonDisplayed: false,
      // NMR
      detailsShown: false,
      titleShown: false,
      // Chat
      isLoading: false,
      isRegenerating: false,
      advancedHidden: true,
      prompt: "",
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
    haveProcessNumberProperties() {
      return this.properties && "processNumber" in this.properties;
    },
    haveChatProperties() {
      return this.properties && "chat" in this.properties;
    },
    modelObj() {
      return this.availableModels[this.modelName] || {};
    },
    tempInvalid() {
      return (
        this.temperature == null ||
        isNaN(this.temperature) ||
        this.temperature < 0 ||
        this.temperature > 1
      );
    },
    estimatedCost() {
      // a rough estimation of cost, assuming the next input will be about 50 tokens
      // and the output will be about 250.
      return (
        (this.modelObj["input_cost_usd_per_MTok"] * (this.tokenCount + 50)) / 1e6 +
        (this.modelObj["output_cost_usd_per_MTok"] * 250) / 1e6
      );
    },
    errorMessage() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .error_message;
    },
    tokenCount() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].token_count;
    },
    file_id: createComputedSetterForBlockField("file_id"),
    wavelength: createComputedSetterForBlockField("wavelength"),
    all_cycles: createComputedSetterForBlockField("cyclenumber"),
    s_spline: createComputedSetterForBlockField("s_spline"),
    win_size_1: createComputedSetterForBlockField("win_size_1"),
    derivative_mode: createComputedSetterForBlockField("derivative_mode"),
    characteristic_mass: createComputedSetterForBlockField("characteristic_mass"),
    selected_process: createComputedSetterForBlockField("selected_process"),
    messages: createComputedSetterForBlockField("messages"),
    temperature: createComputedSetterForBlockField("temperature"),
    modelName: createComputedSetterForBlockField("model"),
    availableModels: createComputedSetterForBlockField("available_models"),
  },
  created() {
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
    console.log(this.haveChatProperties);
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
    console.log("#%#%#%#%#%#%#%%#%#%#%#%#%#%#");
  },
  methods: {
    parseWavelength() {
      if (isNaN(this.wavelength) || isNaN(parseFloat(this.wavelength))) {
        this.wavelengthParseError = "Please provide a valid number";
      } else {
        this.wavelengthParseError = "";
      }
    },
    async updateBlock() {
      if (this.haveChatProperties) {
        this.isLoading = true;
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].prompt =
          this.prompt;
      }
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      )
        .then(() => {
          if (this.haveCycleProperties) {
            this.bokehPlotLimitedWidth = this.derivative_mode != "dQ/dV";
            this.isReplotButtonDisplayed = false;
          }
          if (this.haveChatProperties) {
            this.prompt = "";
          }
        })
        .finally(() => {
          if (this.haveChatProperties) {
            this.isLoading = false;
          }
        });
    },
    lookup_file_field(field, file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.[field];
    },
    async regenerateLastResponse() {
      this.isLoading = true;
      this.isRegenerating = true;
      const last_message = this.messages.pop();
      await updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      ).catch(() => {
        this.messages.push(last_message);
      });
      this.isLoading = false;
      this.isRegenerating = false;
    },
  },
};
</script>

<style scoped>
/* MEDIA */
image,
video {
  display: block;
  max-height: 600px;
}

/* CYCLE */
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

/* NMR */
.attribute-label {
  color: grey;
}

th {
  color: #454545;
  font-weight: 500;
}

/* CHAT */
.context-button {
  cursor: pointer;
  float: right;
}

.send-button {
  height: 2.5rem;
  border-radius: 2rem;
  position: relative;
  left: -70px;
  top: -10px;
  z-index: 10;
}

.regenerate-button {
  margin-top: -1rem;
  margin-bottom: 1rem;
}

.advanced-information {
  margin-left: 20%;
}

.advanced-information label {
  font-weight: 600;
  color: #2c3e50;
}

#model-information-messages {
  font-style: italic;
}
</style>
