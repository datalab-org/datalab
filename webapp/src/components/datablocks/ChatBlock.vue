<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="row">
      <div id="chatWindowContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
        <ChatWindow :chatMessages="messages" />
      </div>
    </div>
    <div class="input-group form-inline col-md-8 mx-auto">
      <textarea
        rows="3"
        type="text"
        class="form-control"
        :disabled="isLoading"
        v-model="prompt"
        @keydown.enter="updateBlock()"
        placeholder="Type your message to send to the LLM, then hit enter when you are ready."
      />
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
    messages() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id].messages;
    },
    prompt: createComputedSetterForBlockField("prompt"),
  },
  components: {
    DataBlockBase,
    ChatWindow,
  },
  methods: {
    updateBlock() {
      this.isLoading = true;
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
      );
      this.isLoading = false;
    },
  },
};
</script>

<style scoped></style>
