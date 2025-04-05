<template>
  <BaseIconCounter :count="count" :icon="['fa', 'file']" :hover-text="hoverText" />
</template>

<script>
import BaseIconCounter from "./BaseIconCounter.vue";

export default {
  name: "FilesIconCounter",
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
  },
  computed: {
    hoverText() {
      return `${this.count} file${this.count !== 1 ? "s" : ""}`;
    },
  },
};
</script>
