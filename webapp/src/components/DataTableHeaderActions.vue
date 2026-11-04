<template>
  <button
    data-testid="clear-filters-button"
    class="clear-filters-button"
    type="button"
    :disabled="!hasActiveFilters"
    :title="hasActiveFilters ? 'Clear all filters' : 'No active filters'"
    aria-label="Clear all filters"
    @click="$emit('clear-filters')"
  >
    <i class="pi pi-filter-slash"></i>
  </button>
</template>

<script>
/**
 * Controls shown in the header of a table's actions column. Clearing the filters is left to
 * the table, which owns the filter state; this only reports the request.
 */
export default {
  name: "DataTableHeaderActions",
  props: {
    hasActiveFilters: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["clear-filters"],
};
</script>

<style scoped>
.clear-filters-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.clear-filters-button:hover {
  opacity: 0.7;
}

.clear-filters-button:disabled {
  color: #ced4da;
  cursor: default;
  opacity: 1;
}
</style>
