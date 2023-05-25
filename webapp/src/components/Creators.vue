<template>
  <span v-for="creator in creators" :key="creator.display_name">
    <UserBubble :creator="creator" :size="'this.size'" />
    <span v-if="showNames && creator.display_name">
      {{ creator.display_name }}
    </span>
  </span>
</template>

<script>
import UserBubble from "@/components/UserBubble.vue";

export default {
  data() {
    return {};
  },
  props: {
    creators: {
      type: Array,
    },
    showNames: {
      type: Boolean,
      default: false,
      required: false,
    },
    size: {
      type: Number,
      default: 24,
      required: false,
    },
  },
  components: {
    UserBubble,
  },
};
</script>
