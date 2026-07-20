<template>
  <StyledTooltip>
    <template #anchor>
      <span class="badge badge-pill tag-badge" :style="tagStyle">
        <font-awesome-icon v-if="isPersonal" :icon="['fas', 'user']" size="xs" class="mr-1" />{{
          tag.name
        }}
      </span>
    </template>
    <template #content>
      <!-- Prefer the tag's description; otherwise fall back to its name. -->
      {{ tag.description || tag.name }}
      <span v-if="isPersonal" class="font-italic">(personal tag)</span>
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
  },
  computed: {
    // A personal tag is marked with a small user icon to distinguish from a global tag.
    isPersonal() {
      return this.tag.scope === "user";
    },
    tagStyle() {
      // When a tag has a color, use it as the badge background with a readable
      // text color; otherwise fall back to the `.tag-badge` default colors.
      const color = this.tag.color;
      return color ? { backgroundColor: color, color: readableTextColor(color) } : {};
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
</style>
