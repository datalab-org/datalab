<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="row">
      <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
        <ChatWindow :chatMessages="messages" :isLoading="isLoading" />
      </div>
    </div>
    <div class="input-group form-inline col-md-10 mx-auto align-items-end">
      <textarea
        rows="3"
        type="text"
        class="form-control"
        :disabled="isLoading"
        v-model="prompt"
        placeholder="Type your message to send to the LLM, then hit send (or shift-enter)."
        @keydown.enter.shift.exact.prevent="updateBlock"
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
    };
  },
  computed: {
    messages: createComputedSetterForBlockField("messages"),
    prompt: createComputedSetterForBlockField("prompt"),
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
  },
};
</script>

<style scoped>
.send-button {
  height: 2.5rem;
  border-radius: 2rem;
  position: relative;
  left: -70px;
  top: -10px;
  z-index: 10;
}
</style>
