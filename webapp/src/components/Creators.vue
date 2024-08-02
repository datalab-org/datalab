<template>
  <span v-for="creator in creators" :key="creator.display_name">
    <span v-if="showBubble">
      <UserBubble v-if="showBubble" :creator="creator" :size="size" />
    </span>
    <span v-if="showNames && creator.display_name && creators.length === 1" class="display-name">
      {{ creator.display_name }}
      <span v-if="creator !== creators[creators.length - 1]">,</span>
    </span>
  </span>
</template>

<script>
import UserBubble from "@/components/UserBubble.vue";

export default {
  components: {
    UserBubble,
  },
  props: {
    creators: {
      type: Array,
      default: () => [],
    },
    showNames: {
      type: Boolean,
      default: true,
      required: false,
    },
    showBubble: {
      type: Boolean,
      default: true,
      required: false,
    },
    size: {
      type: Number,
      default: 24,
      required: false,
    },
  },
  data() {
    return {};
  },
};
</script>

<style scoped>
.display-name {
  margin-left: 0.5em;
}
</style>
