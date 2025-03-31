<template>
  <BaseIconCounter :count="count" :icon="['fa', 'cubes']" :hover-text="hoverText" />
</template>

<script>
import BaseIconCounter from "./BaseIconCounter.vue";

export default {
  name: "BlocksIconCounter",
  components: {
    BaseIconCounter,
  },
  props: {
    count: {
      type: Number,
      default: 0,
    },
    maxDisplay: {
      type: Number,
      default: 99,
    },
    blockInfo: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    hoverText() {
      let block_count_message = `${this.count} block${this.count !== 1 ? "s" : ""}`;
      if (!this.blockInfo || this.blockInfo.length === 0) {
        return block_count_message;
      }
      const blockTypeValues = this.blockInfo.map((item) => item.blocktype).filter(Boolean);
      const uniqueTypes = [...new Set(blockTypeValues)];
      return block_count_message + ": " + uniqueTypes.join(", ");
    },
  },
};
</script>
