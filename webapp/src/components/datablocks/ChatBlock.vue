<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div v-if="advancedHidden" @click="advancedHidden = !advancedHidden" class="context-button">
      [show advanced]
    </div>
    <div v-if="!advancedHidden" @click="advancedHidden = !advancedHidden" class="context-button">
      [hide advanced]
    </div>

    <div class="row">
      <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-12 mx-auto">
        <div class="advanced-information" v-if="!advancedHidden">
          <label>Model</label>: {{ modelName }} <br />
          <label>Current conversation token count</label>: {{ tokenCount }}/4097

          <div class="input-group form-inline">
            <label for="temperatureInput" class="mr-2"><b>temperature:</b></label>
            <input
              id="temperatureInput"
              type="number"
              min="0"
              max="1"
              step="0.1"
              class="form-control-sm"
              v-model="temperature"
              :class="{ 'red-border': tempInvalid }"
            />
            <small class="text-danger" v-show="tempInvalid">
              Temperature must must be a number between 0 and 1
            </small>
          </div>
        </div>
        <ChatWindow :chatMessages="messages.slice(advancedHidden ? 2 : 0)" :isLoading="isLoading" />
        <div class="d-flex justify-content-center">
          <button
            class="btn btn-default btn-sm regenerate-button"
            @click="regenerateLastResponse"
            :disabled="messages[messages.length - 1]['role'] != 'assistant'"
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
    <div v-if="errorMessage" class="alert alert-warning">
      {{ errorMessage }}
    </div>
    <div class="input-group form-inline col-md-10 mx-auto align-items-end">
      <textarea
        rows="3"
        type="text"
        class="form-control"
        :disabled="isLoading"
        v-model="prompt"
        placeholder="Type your message to send to the LLM, then press enter or hit send (shift-enter for newline)."
        @keydown.enter.exact.prevent="updateBlock"
      />
      <button
        type="button"
        class="btn btn-default send-button"
        :disabled="!prompt || isLoading"
        @click="updateBlock()"
      >
        Send
      </button>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import ChatWindow from "@/components/ChatWindow";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  props: {
    item_id: String,
    block_id: String,
  },
  data() {
    return {
      isLoading: false,
      isRegenerating: false,
      advancedHidden: true,
    };
  },
  computed: {
    messages: createComputedSetterForBlockField("messages"),
    prompt: createComputedSetterForBlockField("prompt"),
    temperature: createComputedSetterForBlockField("temperature"),
    tempInvalid() {
      return (
        this.temperature == null ||
        isNaN(this.temperature) ||
        this.temperature < 0 ||
        this.temperature > 1
      );
    },

    errorMessage() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .error_message;
    },
    tokenCount() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].token_count;
    },
    modelName() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].model_name;
    },
  },
  components: {
    DataBlockBase,
    ChatWindow,
  },
  methods: {
    async updateBlock() {
      this.isLoading = true;
      this.messages.push({
        content: this.prompt,
        role: "user",
      });
      this.prompt = "";

      await updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
      );
      this.isLoading = false;
    },
    async regenerateLastResponse() {
      this.isLoading = true;
      this.isRegenerating = true;
      const last_message = this.messages.pop();
      await updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
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
