<template>
  <StyledTooltip>
    <template #anchor>
      <span
        class="badge badge-pill tag-badge"
        :class="{ 'tag-badge--clickable': clickable }"
        :role="clickable ? 'button' : null"
        :style="tagStyle"
        @click="onClick"
      >
        <font-awesome-icon v-if="scopeIcon" :icon="['fas', scopeIcon]" size="xs" class="mr-1" />{{
          tag.name
        }}
      </span>
    </template>
    <template #content>
      <!-- Prefer the tag's description; otherwise fall back to its name. -->
      {{ tag.description || tag.name }}
      <span v-if="scopeNote" class="font-italic">({{ scopeNote }})</span>
    </template>
  </StyledTooltip>
</template>

<script>
import { readableTextColor } from "@/field_utils.js";
import StyledTooltip from "@/components/StyledTooltip.vue";

export default {
  name: "TagBadge",
  components: {
    StyledTooltip,
  },
  props: {
    // A tag is a reference object `{ type: "tags", immutable_id, name, color, description }`.
    tag: {
      type: Object,
      required: true,
    },
    // When true, the badge is a button that emits `tag-click` and gets a hover border.
    clickable: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["tag-click"],
  computed: {
    // User-defined and group tags are marked with a small icon to distinguish them from
    // global tags.
    scopeIcon() {
      return { user: "user", group: "users" }[this.tag.scope] || null;
    },
    // Tooltip note naming the owner (display-only `owner_name`) of user-defined and group tags.
    scopeNote() {
      const owner = this.tag.owner_name;
      if (this.tag.scope === "user") {
        return owner ? `user-defined tag of ${owner}` : "user-defined tag";
      }
      if (this.tag.scope === "group") {
        return owner ? `group tag of ${owner}` : "group tag";
      }
      return null;
    },
    tagStyle() {
      // When a tag has a color, use it as the badge background with a readable
      // text color; otherwise fall back to the `.tag-badge` default colors.
      const color = this.tag.color;
      return color ? { backgroundColor: color, color: readableTextColor(color) } : {};
    },
  },
  methods: {
    onClick(event) {
      if (!this.clickable) {
        return;
      }
      // Stop the row-click navigation and filter by this tag instead.
      event.stopPropagation();
      this.$emit("tag-click", this.tag);
    },
  },
};
</script>

<style scoped>
.tag-badge {
  font-size: 0.85em;
  font-weight: 500;
  /* Default badge colors, used when the tag has no color of its own. */
  background-color: #d1e7dd;
  color: #0f5132;
}
.tag-badge--clickable {
  cursor: pointer;
  /* Reserve the border box so the hover border doesn't shift the layout. */
  border: 2px solid transparent;
  transition: border 0.25s ease;
}
.tag-badge--clickable:hover {
  /* Match the creators-column avatar hover affordance (UserBubble.vue). */
  border-color: black;
  box-shadow: 0 0 5px 0 skyblue;
}
</style>
