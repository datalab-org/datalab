<template>
  <div v-for="creator in creators" :key="creator.display_name">
    <UserBubble :creator="creator" :size="this.size" />
  </div>
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
    size: {
      type: String,
      default: "24",
      required: false,
    },
  },
  components: {
    UserBubble,
  },
};
</script>
