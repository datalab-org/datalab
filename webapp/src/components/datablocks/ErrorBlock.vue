<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="alert alert-danger d-flex align-items-center ml-3">
      <font-awesome-icon icon="exclamation-triangle" class="mr-2" />
      <span v-html="error" />
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase.vue";

export default {
  components: {
    DataBlockBase,
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
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    not_implemented_error() {
      return (
        "The requested block type '" +
        this.blockType +
        "' is not implemented/installed for this <i>datalab</i> instance. Please contact your <i>datalab</i> administrator."
      );
    },
    error() {
      let error_message = this.$store.state.block_errors[this.block_id];
      if (!error_message) {
        error_message = this.not_implemented_error;
      }
      return error_message;
    },
    blockType() {
      return this.block?.blocktype;
    },
  },
};
</script>
