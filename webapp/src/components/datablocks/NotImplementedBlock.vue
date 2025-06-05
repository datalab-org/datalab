<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="alert alert-danger d-flex align-items-center ml-3">
      <font-awesome-icon icon="exclamation-triangle" class="mr-2" />
      This block type ({{ blockType }}) is not implemented/installed for
      this&nbsp;<i>datalab</i>&nbsp;instance. Please contact
      your&nbsp;<i>datalab</i>&nbsp;administrator.
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
    blockType() {
      return this.block?.blocktype;
    },
  },
};
</script>
