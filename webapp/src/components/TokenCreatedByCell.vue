<template>
  <div v-if="creator" class="d-flex align-items-center">
    <UserBubble :creator="creator" :size="24" />
    <span class="ms-2">{{ creator.display_name }}</span>
  </div>
  <span v-else class="text-muted">Unknown</span>
</template>

<script>
import UserBubble from "@/components/UserBubble.vue";

export default {
  name: "TokenCreatedByCell",
  components: {
    UserBubble,
  },
  props: {
    creator: {
      type: Object,
      required: false,
      default: null,
    },
  },
};
</script>
