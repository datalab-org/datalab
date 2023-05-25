<template>
  <span v-for="creator in creators" :key="creator.display_name">
    <span v-if="showBubble">
      <UserBubble :creator="creator" :size="size" v-if="showBubble" />
    </span>
    <span class="display-name" v-if="showNames && creator.display_name">
      {{ creator.display_name }}
      <span v-if="creator !== creators[creators.length - 1]">,</span>
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
  components: {
    UserBubble,
  },
};
</script>

<style scoped>
.display-name {
  margin-left: 0.5em;
}
</style>
