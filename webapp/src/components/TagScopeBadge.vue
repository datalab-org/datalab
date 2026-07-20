<template>
  <span
    class="badge badge-pill"
    :class="isPersonal ? 'badge-info' : 'badge-secondary'"
    data-testid="tag-scope-badge"
  >
    <font-awesome-icon v-if="isPersonal" :icon="['fas', 'user']" class="mr-1" />
    {{ isPersonal ? "Personal" : "Global" }}
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
    isPersonal() {
      return this.tag.scope === "user";
    },
  },
};
</script>
