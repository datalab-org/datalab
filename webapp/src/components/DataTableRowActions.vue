<template>
  <div class="row-actions">
    <button
      v-for="action in actions"
      :key="action.key"
      :data-testid="`row-${action.key}-button`"
      class="row-action-button"
      type="button"
      :title="action.rowLabel"
      :aria-label="`${action.rowLabel} ${rowLabel}`"
      @click.stop="$emit('action-request', { action: action.key, items: [row], source: 'row' })"
    >
      <font-awesome-icon :icon="action.icon" />
    </button>
  </div>
</template>

<script>
/**
 * The action buttons shown on a single table row, one per action descriptor (see
 * `utils/itemActions.js`).
 *
 * Clicking an action only emits an `action-request`; carrying it out is up to the table.
 */
export default {
  name: "DataTableRowActions",
  props: {
    row: {
      type: Object,
      required: true,
    },
    actions: {
      type: Array,
      required: true,
    },
  },
  emits: ["action-request"],
  computed: {
    // Names the row in each button's accessible label, so screen readers announce e.g.
    // "Delete sample1" rather than a list of identical "Delete" buttons.
    rowLabel() {
      return this.row.item_id || this.row.collection_id || this.row.name || "";
    },
  },
};
</script>

<style scoped>
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.row-action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.row-action-button:hover {
  opacity: 0.7;
}
</style>
