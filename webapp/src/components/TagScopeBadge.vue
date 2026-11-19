<template>
  <span class="badge badge-pill" :class="badgeClass" data-testid="tag-scope-badge">
    <font-awesome-icon v-if="icon" :icon="['fas', icon]" class="mr-1" />
    {{ label }}
  </span>
</template>

<script>
export default {
  name: "TagScopeBadge",
  props: {
    // A tag row from GET /tags, carrying `scope` ("global" | "user" | "group") and, for
    // user and group tags, the display-only `owner_name`.
    tag: {
      type: Object,
      required: true,
    },
  },
  computed: {
    badgeClass() {
      return (
        {
          user: "badge-info",
          group: "badge-dark",
        }[this.tag.scope] || "badge-secondary"
      );
    },
    icon() {
      return { user: "user", group: "users" }[this.tag.scope] || null;
    },
    label() {
      const base = { user: "User-defined", group: "Group" }[this.tag.scope] || "Global";
      return this.tag.owner_name && this.tag.scope !== "global"
        ? `${base}: ${this.tag.owner_name}`
        : base;
    },
  },
};
</script>
