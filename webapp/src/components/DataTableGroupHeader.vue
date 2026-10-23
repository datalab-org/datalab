<template>
  <button
    type="button"
    class="group-header btn btn-link p-0 text-reset font-weight-bold"
    :style="{ marginLeft: `${group.depth * 1.5}rem` }"
    :aria-expanded="expanded"
    data-testid="group-header"
    @click.stop="$emit('toggle')"
  >
    <font-awesome-icon
      :icon="expanded ? 'chevron-down' : 'chevron-right'"
      fixed-width
      class="mr-1"
    />
    {{ label }}
    <span class="badge badge-secondary badge-pill ml-1">{{ group.count }}</span>
  </button>
</template>

<script>
export default {
  name: "DataTableGroupHeader",
  props: {
    // A group of `buildGroupTree` in `utils/tableGrouping.js`.
    group: {
      type: Object,
      required: true,
    },
    expanded: {
      type: Boolean,
      required: true,
    },
    // Whether to name the parent groups too, e.g. at the top of a page continuing them.
    withParents: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ["toggle"],
  computed: {
    label() {
      const labels = [this.group.label];
      for (let parent = this.group.parent; this.withParents && parent; parent = parent.parent) {
        labels.unshift(parent.label);
      }
      return labels.join(" › ");
    },
  },
};
</script>

<style scoped>
.group-header {
  text-decoration: none;
}
</style>
