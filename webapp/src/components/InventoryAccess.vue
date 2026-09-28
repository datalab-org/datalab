<template>
  <div class="d-flex align-items-center">
    <Creators :creators="creators" :groups="groups" :show-names="false" show-bubble />
    <span
      v-if="groups.length === 0"
      class="text-muted small"
      :class="{ 'ml-1': creators.length > 0 }"
      title="Not restricted to any groups, so all users can access this item"
    >
      Everyone
    </span>
  </div>
</template>

<script>
import Creators from "@/components/Creators";

export default {
  components: { Creators },
  props: {
    creators: { type: Array, default: () => [] },
    groups: { type: Array, default: () => [] },
  },
};
</script>
