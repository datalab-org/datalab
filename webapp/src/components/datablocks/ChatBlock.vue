<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div v-if="advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
      [show advanced]
    </div>
    <div v-if="!advancedHidden" class="context-button" @click="advancedHidden = !advancedHidden">
      [hide advanced]
    </div>

    <div class="row">
      <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-12 mx-auto">
        <div v-if="!advancedHidden" class="advanced-information">
          <div class="row mt-2 mb-2 align-items-center">
            <div class="col-auto">
              <label class="form-label">Model:</label>
            </div>
            <div class="col-auto">
              <select v-model="modelName" class="form-control">
                <option v-for="model in Object.keys(availableModels)" :key="model">
                  {{ model }}
                </option>
              </select>
            </div>
          </div>
          <div class="row mt-2 mb-2 align-items-center">
            <div class="col-auto">
              <label class="form-label">Current conversation token count:</label>
            </div>
            <div class="col-auto">
              <span class="ps-1">{{ tokenCount }}/ {{ modelObj.context_window }}</span>
            </div>
          </div>
          <div class="row mt-2 mb-2 align-items-center">
            <div class="col-auto">
              <label class="form-label">est. cost for next message:</label>
            </div>
            <div class="col-auto">
              <span class="ps-1">${{ estimatedCost.toPrecision(2) }}</span>
            </div>
          </div>

          <div class="row mt-2 mb-2 align-items-center">
            <div class="col-auto">
              <label for="temperatureInput" class="form-label"><b>temperature:</b></label>
            </div>
            <div class="col-auto">
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
            </div>
            <div class="col-auto">
              <small v-show="tempInvalid" class="text-danger">
                Temperature must must be a number between 0 and 1
              </small>
            </div>
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
              class="pe-1 text-muted"
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

    <div class="row col-md-10 mx-auto align-items-end">
      <div class="col-10 pe-0">
        <textarea
          v-model="prompt"
          rows="3"
          type="text"
          class="form-control"
          :disabled="isLoading"
          placeholder="Type your message to send to the LLM, then press enter or hit send (shift-enter for newline)."
          @keydown.enter.exact.prevent="updateBlock"
        />
      </div>
      <div class="col-2 ps-0">
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
import ChatWindow from "@/components/ChatWindow";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
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
      isLoading: false,
      isRegenerating: false,
      advancedHidden: true,
      prompt: "",
    };
  },
  computed: {
    messages: createComputedSetterForBlockField("messages"),
    temperature: createComputedSetterForBlockField("temperature"),
    modelName: createComputedSetterForBlockField("model"),
    availableModels: createComputedSetterForBlockField("available_models"),
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
  },
  methods: {
    async updateBlock() {
      this.isLoading = true;
      this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].prompt =
        this.prompt;

      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      )
        .then(() => {
          this.prompt = "";
        })
        .finally(() => {
          this.isLoading = false;
        });
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
