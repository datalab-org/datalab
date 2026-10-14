<template>
  <div class="dropdown-menu dropdown-menu-right show" @click.stop>
    <div class="d-flex">
      <div class="flex-fill border-right">
        <h6 class="dropdown-header">Filters</h6>
        <button
          v-for="f in resolvedQuickFilters"
          :key="f.id"
          type="button"
          class="dropdown-item"
          :class="{ active: activeFilters.includes(f.id), disabled: f.disabled }"
          :disabled="f.disabled"
          :title="f.disabled ? 'Not applicable to this table' : ''"
          @click="toggleFilter(f.id)"
        >
          {{ f.label }}
        </button>
        <div class="dropdown-divider"></div>
        <button type="button" class="dropdown-item" @click="$emit('open-advanced-query')">
          <font-awesome-icon icon="filter" class="mr-2" />Custom filter…
        </button>
      </div>

      <div class="flex-fill">
        <h6 class="dropdown-header">Group by</h6>
        <button
          v-for="g in resolvedStaticGroupFields"
          :key="g.id"
          type="button"
          class="dropdown-item"
          :class="{ active: isGroupActive(g.id), disabled: g.disabled }"
          :disabled="g.disabled"
          :title="g.disabled ? 'Not applicable to this table' : ''"
          @click="toggleGroup(g)"
        >
          {{ g.label }}
        </button>

        <div v-if="isGroupActive('date')" class="px-4 py-1">
          <div class="btn-group btn-group-sm" role="group" aria-label="Date grouping">
            <button
              v-for="grain in dateGrains"
              :key="grain"
              type="button"
              class="btn text-capitalize"
              :class="dateGrain === grain ? 'btn-primary' : 'btn-outline-primary'"
              @click="setDateGrain(grain)"
            >
              {{ grain }}
            </button>
          </div>
        </div>

        <div class="dropdown-divider"></div>
        <button
          type="button"
          class="dropdown-item dropdown-toggle"
          :aria-expanded="isCustomGroupOpen"
          @click="isCustomGroupOpen = !isCustomGroupOpen"
        >
          Custom group
        </button>
        <template v-if="isCustomGroupOpen">
          <span v-if="customGroupFieldsLoading" class="dropdown-item-text text-muted">
            Loading…
          </span>
          <span v-else-if="!customGroupFields.length" class="dropdown-item-text text-muted">
            No other groupable fields
          </span>
          <button
            v-for="f in customGroupFields"
            :key="f.id"
            type="button"
            class="dropdown-item"
            :class="{ active: isGroupActive(f.id) }"
            @click="toggleGroup(f)"
          >
            {{ f.label }}
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { QUICK_FILTERS, STATIC_GROUP_FIELDS } from "@/quickSearchOptions.js";
import { fetchQuerySchema } from "@/server_fetch_utils.js";

export default {
  name: "AdvancedSearchDropdown",
  props: {
    activeFilters: { type: Array, required: true },
    groupByFields: { type: Array, required: true },
    availableColumns: { type: Array, default: () => [] },
    advancedQueryConfig: { type: Object, default: null },
  },
  emits: ["update:active-filters", "update:group-by-fields", "open-advanced-query"],
  data() {
    return {
      isCustomGroupOpen: false,
      quickFilters: QUICK_FILTERS,
      staticGroupFields: STATIC_GROUP_FIELDS,
      dateGrains: ["day", "week", "month", "year"],
      // Groupable fields beyond the static list, fetched from this data type's query
      // schema. Owned here (not by the parent toolbar) since only this dropdown uses them.
      customGroupFields: [],
      customGroupFieldsLoading: false,
    };
  },
  computed: {
    columnFields() {
      return new Set(this.availableColumns.map((c) => c.field));
    },
    resolvedQuickFilters() {
      return this.quickFilters.map((f) => ({ ...f, disabled: !this.isApplicable(f) }));
    },
    resolvedStaticGroupFields() {
      return this.staticGroupFields.map((f) => ({ ...f, disabled: !this.isApplicable(f) }));
    },
    dateGrain() {
      const entry = this.groupByFields.find((g) => g.id === "date");
      return entry?.grain || "month";
    },
  },
  watch: {
    advancedQueryConfig: {
      immediate: true,
      handler() {
        this.loadCustomGroupFields();
      },
    },
  },
  methods: {
    async loadCustomGroupFields() {
      if (!this.advancedQueryConfig || !this.advancedQueryConfig.isEnabled) {
        this.customGroupFields = [];
        return;
      }
      this.customGroupFieldsLoading = true;
      try {
        // Groupable properties shared by every type this table can search.
        const fieldLists = await Promise.all(
          this.advancedQueryConfig.types.map(async (t) => (await fetchQuerySchema(t.id)).fields),
        );
        const fields = fieldLists[0].filter((f) =>
          fieldLists.every((list) => list.some((other) => other.id === f.id)),
        );
        const loadedFieldIds = new Set(this.availableColumns.map((c) => c.field));
        const staticFieldIds = new Set(["tags", "type", "creators", "status", "date"]);
        this.customGroupFields = fields
          .filter((f) => f.groupable && loadedFieldIds.has(f.id) && !staticFieldIds.has(f.id))
          .map((f) => ({ id: f.id, label: f.label }));
      } catch (error) {
        console.error("Failed to load groupable fields:", error);
        this.customGroupFields = [];
      } finally {
        this.customGroupFieldsLoading = false;
      }
    },
    // Whether this table shows one of the columns a quick filter or group-by field reads.
    isApplicable(option) {
      return !option.columns || option.columns.some((c) => this.columnFields.has(c));
    },
    toggleFilter(id) {
      const next = this.activeFilters.includes(id)
        ? this.activeFilters.filter((f) => f !== id)
        : [...this.activeFilters, id];
      this.$emit("update:active-filters", next);
    },
    isGroupActive(id) {
      return this.groupByFields.some((g) => g.id === id);
    },
    toggleGroup(field) {
      if (field.disabled) return;
      const exists = this.isGroupActive(field.id);
      const next = exists
        ? this.groupByFields.filter((g) => g.id !== field.id)
        : [...this.groupByFields, { id: field.id, label: field.label, grain: "month" }];
      this.$emit("update:group-by-fields", next);
    },
    setDateGrain(grain) {
      const next = this.groupByFields.map((g) => (g.id === "date" ? { ...g, grain } : g));
      this.$emit("update:group-by-fields", next);
    },
  },
};
</script>
