<template>
  <span
    class="badge badge-pill"
    :class="isUserDefined ? 'badge-info' : 'badge-secondary'"
    data-testid="tag-scope-badge"
  >
    <font-awesome-icon v-if="isUserDefined" :icon="['fas', 'user']" class="mr-1" />
    {{ isUserDefined ? "User-defined" : "Global" }}
  </span>
</template>

<script>
export default {
  name: "TagScopeBadge",
  props: {
    // A tag row from GET /tags, carrying `scope` ("global" | "user").
    tag: {
      type: Object,
      required: true,
    },
  },
  computed: {
    isUserDefined() {
      return this.tag.scope === "user";
    },
  },
};
</script>
