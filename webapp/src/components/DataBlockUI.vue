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
      <div v-for="(prop, propKey) in properties" :key="propKey">
        <div v-if="prop.type === 'float'" class="form-row col-md-6 col-lg-4 mt-2 mb-2 pl-0">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ prop.label }}</b></label
            >
            <input
              v-model="propertyValues[propKey]"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': validationErrors[propKey] }"
              @keydown.enter="
                validateProperty(propKey);
                updateBlock();
              "
              @blur="
                validateProperty(propKey);
                updateBlock();
              "
            />
            <div v-if="validationErrors[propKey]" class="alert alert-danger mt-2 mx-auto">
              {{ validationErrors[propKey] }}
            </div>
          </div>
        </div>

        <div v-if="prop.type === 'string'" class="form-row">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ prop.label }}</b></label
            >
            <input
              v-model="propertyValues[propKey]"
              type="text"
              class="form-control"
              :placeholder="prop.placeholder || ''"
              :class="{ 'is-invalid': validationErrors[propKey] }"
              @keydown.enter="
                validateProperty(propKey);
                updateBlock();
              "
              @blur="
                validateProperty(propKey);
                updateBlock();
              "
            />
            <span v-if="propKey === 'cycle'" id="list-of-cycles" class="pl-3 pt-2">
              Showing cycles: {{ parsedCycles }}
            </span>
          </div>
          <div v-if="validationErrors[propKey]" class="alert alert-danger mt-2 mx-auto">
            {{ validationErrors[propKey] }}
          </div>
        </div>

        <div v-if="prop.type === 'selector'" class="form-row mt-2">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ prop.label || "Mode:" }}</b></label
            >
            <div class="btn-group">
              <div
                v-for="option in prop.options"
                :key="option.value"
                class="btn btn-default"
                :class="{ active: propertyValues[propKey] === option.value }"
                @click="
                  propertyValues[propKey] =
                    propertyValues[propKey] === option.value ? null : option.value;
                  updateBlock();
                "
                v-html="option.label"
              ></div>
            </div>
          </div>
        </div>

        <div v-if="prop.type === 'slider' && shouldShowSliders" class="row">
          <div class="col-md slider" style="max-width: 250px">
            <input
              :id="propKey"
              v-model="propertyValues[propKey]"
              type="range"
              class="form-control-range"
              :name="propKey"
              :min="prop.min"
              :max="prop.max"
              :step="prop.step"
              @change="isReplotButtonDisplayed = true"
            />
            <label
              :for="propKey"
              @mouseover="descriptionVisible[propKey] = true"
              @mouseleave="descriptionVisible[propKey] = false"
            >
              <span>{{ prop.label }}</span>
              {{ propKey === "s_spline" ? `-${propertyValues[propKey]}` : propertyValues[propKey] }}
            </label>
          </div>
          <div v-if="descriptionVisible[propKey]" class="alert alert-info">
            <p>{{ prop.description }}</p>
          </div>
        </div>

        <div v-if="prop.type === 'select'" class="form-inline mt-2">
          <div class="form-group">
            <label class="mr-2"
              ><b>{{ prop.label }}</b></label
            >
            <select v-model="propertyValues[propKey]" class="form-control" @change="updateBlock">
              <option v-for="option in getSelectOptions(prop)" :key="option">
                {{ option }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="prop.type === 'toggleDetails'" class="mt-4">
          <span v-if="blockType === 'nmr'" class="mr-2">
            <Isotope :isotope-string="block_data.nucleus" /> {{ block_data.pulse_program_name }}
          </span>
          <div>
            <a
              v-for="toggle in prop.toggles"
              :key="toggle.key"
              type="button"
              class="btn btn-default btn-sm mb-2 ml-2"
              @click="propertyValues[toggle.key] = !propertyValues[toggle.key]"
            >
              {{ propertyValues[toggle.key] ? toggle.hideLabel : toggle.label }}
            </a>
          </div>
        </div>
      </div>

      <div v-if="blockType === 'nmr' && propertyValues.titleShown" class="card mb-2">
        <div class="card-body" style="white-space: pre">
          {{ block_data.topspin_title }}
        </div>
      </div>

      <div v-if="hasBokehPlot">
        <div class="row">
          <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
            <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
            <div v-else class="alert alert-secondary">
              Plotting currently not available for data with dimension > 1
            </div>
          </div>

          <div
            v-if="blockType === 'nmr' && propertyValues.detailsShown"
            class="col-xl-4 col-lg-4 ml-0"
          >
            <table class="table table-sm">
              <tbody>
                <tr v-for="(value, key) in getNMRDetails()" :key="key">
                  <th scope="row">{{ key }}</th>
                  <td v-html="value"></td>
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

    <div v-if="hasChatProperty">
      <div v-if="advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
        [show advanced]
      </div>
      <div v-if="!advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
        [hide advanced]
      </div>

      <div class="row">
        <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-12 mx-auto">
          <div v-if="!advancedHidden" class="advanced-information">
            <div v-if="chatProperties.advanced.modelSelector" class="input-group">
              <label class="mr-2">Model:</label>
              <select v-model="modelName" class="form-control">
                <option v-for="model in Object.keys(availableModels)" :key="model">
                  {{ model }}
                </option>
              </select>
            </div>
            <br />
            <div v-if="chatProperties.advanced.tokenCount" class="input-group">
              <label>Current conversation token count:</label>
              <span class="pl-1">{{ tokenCount }}/ {{ modelObj.context_window }}</span>
            </div>
            <div v-if="chatProperties.advanced.costEstimation" class="form-row input-group">
              <label>est. cost for next message:</label>
              <span class="pl-1">${{ estimatedCost.toPrecision(2) }}</span>
            </div>

            <div v-if="chatProperties.advanced.temperature" class="form-row input-group">
              <label for="temperatureInput" class="mr-2"><b>temperature:</b></label>
              <input
                id="temperatureInput"
                v-model="temperature"
                type="number"
                :min="chatProperties.advanced.temperature.min"
                :max="chatProperties.advanced.temperature.max"
                :step="chatProperties.advanced.temperature.step"
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

    <button v-if="isReplotButtonDisplayed" class="btn btn-default my-4" @click="updateBlock">
      Recalculate
    </button>
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
      validationErrors: {},
      propertyValues: {},
      descriptionVisible: {},
      isReplotButtonDisplayed: false,
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
    blockType() {
      return this.block_data?.blocktype || "";
    },
    properties() {
      return this.block_data?.blocktype ? blockTypes[this.block_data.blocktype]?.properties : {};
    },
    hasBokehPlot() {
      return this.properties && Object.values(this.properties).some((prop) => prop.type === "plot");
    },
    hasChatProperty() {
      return this.properties && Object.values(this.properties).some((prop) => prop.type === "chat");
    },
    chatProperties() {
      if (!this.hasChatProperty) return {};
      return Object.values(this.properties).find((prop) => prop.type === "chat") || {};
    },
    bokehPlotData() {
      if (!this.file_id) return null;
      return (
        this.$store.state.all_item_data[this.item_id]?.["blocks_obj"]?.[this.block_id]
          ?.bokeh_plot_data || null
      );
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
    shouldShowSliders() {
      return (
        this.blockType === "cycle" &&
        (this.propertyValues.derivativeMode === "dQ/dV" ||
          this.propertyValues.derivativeMode === "dV/dQ")
      );
    },
    parsedCycles() {
      return this.propertyValues.cyclenumber ? this.propertyValues.cyclenumber : "all";
    },
    modelObj() {
      return this.availableModels[this.modelName] || {};
    },
    tempInvalid() {
      const temp = parseFloat(this.temperature);
      return this.temperature == null || isNaN(temp) || temp < 0 || temp > 1;
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
    messages: createComputedSetterForBlockField("messages"),
    temperature: createComputedSetterForBlockField("temperature"),
    modelName: createComputedSetterForBlockField("model"),
    availableModels: createComputedSetterForBlockField("available_models"),
  },
  created() {
    this.initPropertyValues();
  },
  methods: {
    initPropertyValues() {
      if (!this.properties) return;

      Object.keys(this.properties).forEach((key) => {
        if (this.properties[key].type === "toggleDetails") {
          this.properties[key].toggles.forEach((toggle) => {
            this.$set(this.propertyValues, toggle.key, this.block_data[toggle.key] || false);
          });
        } else {
          const value = this.block_data[key] || this.properties[key].default || null;
          this.$set(this.propertyValues, key, value);
        }

        this.$set(this.descriptionVisible, key, false);
      });
    },
    validateProperty(propKey) {
      const prop = this.properties[propKey];
      let error = null;

      if (prop.type === "float") {
        if (
          isNaN(this.propertyValues[propKey]) ||
          isNaN(parseFloat(this.propertyValues[propKey]))
        ) {
          error = "Please provide a valid number";
        }
      }

      this.$set(this.validationErrors, propKey, error);
      return !error;
    },
    getSelectOptions(prop) {
      if (prop.optionsFrom && this.block_data[prop.optionsFrom]) {
        return this.block_data[prop.optionsFrom];
      }
      return [];
    },
    getNMRDetails() {
      if (this.blockType !== "nmr") return {};

      return {
        nucleus: `<Isotope isotope-string="${this.block_data.nucleus}" />`,
        "pulse program": this.block_data.pulse_program_name,
        "Data shape": `${this.block_data.processed_data_shape} (<i>d</i> = ${this.block_data.processed_data_shape.length})`,
        probe: `${this.block_data.probe_name} s`,
        "# of scans": this.block_data.nscans,
        "recycle delay": `${this.block_data.recycle_delay} s`,
        "carrier frequency": `${this.block_data.carrier_frequency_MHz} MHz`,
        "carrier offset": `${(this.block_data.carrier_offset_Hz / this.block_data.carrier_frequency_MHz).toFixed(1)} ppm`,
        cnst31: this.block_data.CNST31,
      };
    },
    async updateBlock() {
      Object.keys(this.propertyValues).forEach((key) => {
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id][key] =
          this.propertyValues[key];
      });

      if (this.hasChatProperty) {
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
          if (this.blockType === "cycle") {
            this.isReplotButtonDisplayed = false;
          }
          if (this.hasChatProperty) {
            this.prompt = "";
          }
          this.initPropertyValues();
        })
        .finally(() => {
          if (this.hasChatProperty) {
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
