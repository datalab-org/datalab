<template>
  <Creators v-if="user" :creators="[user]" :show-bubble="true" :show-names="true" :size="24" />
  <span v-else class="text-muted">{{ fallback }}</span>
</template>

<script>
import Creators from "@/components/Creators.vue";

export default {
  name: "NotificationUserCell",
  components: { Creators },
  props: {
    user: { type: Object, default: null },
    fallback: { type: String, default: "Unknown" },
  },
};
</script>
