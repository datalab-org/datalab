<template>
  <div
    v-if="config"
    v-on-click-outside="() => (isDropdownVisible = false)"
    class="dropdown search-field"
  >
    <div class="input-group">
      <div class="input-group-prepend">
        <span class="input-group-text">
          <font-awesome-icon :icon="isSearching ? 'sync' : 'search'" :spin="isSearching" />
        </span>
        <span v-if="chips.length" class="input-group-text py-0">
          <!-- Only the label is truncated, so the remove button stays visible. -->
          <span
            v-for="chip in chips"
            :key="chip.key"
            class="badge badge-primary d-inline-flex align-items-center mr-1"
            style="max-width: 12rem"
            :title="chip.label"
          >
            <span class="text-truncate" style="min-width: 0">{{ chip.label }}</span>
            <button
              type="button"
              class="btn btn-link p-0 ml-1 text-white flex-shrink-0"
              aria-label="Remove"
              title="Remove"
              @click.stop="chip.clear"
            >
              &times;
            </button>
          </span>
        </span>
      </div>
      <input
        :value="search"
        data-testid="search-input"
        class="form-control"
        :class="{ 'is-invalid': searchError }"
        placeholder="Search"
        @input="$emit('update:search', $event.target.value)"
      />
      <div class="input-group-append">
        <button
          data-testid="advanced-search-chevron"
          type="button"
          class="btn btn-outline-secondary dropdown-toggle"
          aria-label="Search options"
          title="Search options"
          aria-haspopup="true"
          :aria-expanded="isDropdownVisible"
          @click="isDropdownVisible = !isDropdownVisible"
        ></button>
      </div>
      <div v-if="searchError" class="invalid-feedback" data-testid="advanced-search-error">
        {{ searchError }}
      </div>
    </div>

    <AdvancedSearchDropdown
      v-if="isDropdownVisible"
      :active-filters="activeQuickFilters"
      :group-by-fields="groupByFields"
      :available-columns="availableColumns"
      :advanced-query-config="config"
      @update:active-filters="setQuickFilters"
      @update:group-by-fields="$emit('update:group-by-fields', $event)"
      @open-advanced-query="openQueryBuilder"
    />
    <AdvancedQueryBuilder ref="queryBuilder" :types="config.types" @apply="applyQuery" />
  </div>

  <IconField v-else class="search-field">
    <InputIcon>
      <font-awesome-icon icon="search" />
    </InputIcon>
    <InputText
      :model-value="search"
      data-testid="search-input"
      class="search-input"
      placeholder="Search"
      @update:model-value="$emit('update:search', $event)"
    />
  </IconField>
</template>

<script>
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import { vOnClickOutside } from "@vueuse/components";

import AdvancedQueryBuilder from "@/components/AdvancedQueryBuilder.vue";
import AdvancedSearchDropdown from "@/components/AdvancedSearchDropdown.vue";
import { QUICK_FILTERS } from "@/quickSearchOptions.js";
import { fetchAdvancedQueryConfig, runQueryAllPages } from "@/server_fetch_utils.js";
import { rowKey } from "@/utils/tableColumns.js";

// At most this many results of each searched type are shown in the table.
const MAX_RESULTS = 2000;

/**
 * The search box of a table, with its advanced search when the server offers one for the
 * table: quick filters and a custom OPTIMADE filter, run together on the server, and the
 * group-by fields. It emits the keys of the matching rows (`update:result-keys`, null when
 * nothing is searched for), so the table only has to show those rows.
 */
export default {
  name: "AdvancedSearchControl",
  directives: {
    onClickOutside: vOnClickOutside,
  },
  components: {
    AdvancedQueryBuilder,
    AdvancedSearchDropdown,
    IconField,
    InputIcon,
    InputText,
  },
  props: {
    dataType: {
      type: String,
      required: true,
    },
    // The table's global search text.
    search: {
      type: String,
      required: false,
      default: null,
    },
    groupByFields: {
      type: Array,
      required: true,
    },
    availableColumns: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:search", "update:result-keys", "update:group-by-fields"],
  data() {
    return {
      config: null,
      isDropdownVisible: false,
      activeQuickFilters: [],
      // The custom filter applied from the query builder, `{ typeId, filter }`.
      appliedQuery: null,
      isSearching: false,
      searchError: null,
      resultSummary: null,
      // Bumped by each request, so that only the latest one is applied.
      configRequestId: 0,
      searchRequestId: 0,
    };
  },
  computed: {
    chips() {
      const chips = [];
      if (this.resultSummary) {
        chips.push({ key: "query", label: this.resultSummary, clear: this.clearQuery });
      }
      if (this.activeQuickFilters.length) {
        chips.push({
          key: "quick-filters",
          label: this.activeQuickFilters
            .map((id) => QUICK_FILTERS.find((f) => f.id === id).label)
            .join(", "),
          clear: () => this.setQuickFilters([]),
        });
      }
      if (this.groupByFields.length) {
        chips.push({
          key: "group-by",
          label: `Group: ${this.groupByFields.map((g) => g.label).join(" › ")}`,
          clear: () => this.$emit("update:group-by-fields", []),
        });
      }
      return chips;
    },
  },
  watch: {
    dataType: {
      immediate: true,
      handler() {
        this.reset();
        this.loadConfig();
      },
    },
  },
  methods: {
    reset() {
      this.searchRequestId++;
      this.isDropdownVisible = false;
      this.activeQuickFilters = [];
      this.appliedQuery = null;
      this.isSearching = false;
      this.searchError = null;
      this.resultSummary = null;
      this.$emit("update:result-keys", null);
      this.$emit("update:group-by-fields", []);
    },
    async loadConfig() {
      const requestId = ++this.configRequestId;
      this.config = null;
      try {
        const config = await fetchAdvancedQueryConfig(this.dataType);
        if (requestId === this.configRequestId) this.config = config;
      } catch (error) {
        // The plain search box still works without it.
        console.error("Failed to load the advanced search:", error);
      }
    },
    openQueryBuilder() {
      this.isDropdownVisible = false;
      this.$refs.queryBuilder.open();
    },
    setQuickFilters(ids) {
      this.activeQuickFilters = ids;
      this.runSearch();
    },
    applyQuery(query) {
      this.appliedQuery = query;
      this.runSearch();
    },
    clearQuery() {
      this.$refs.queryBuilder.clearFilters();
      this.applyQuery(null);
    },
    async runSearch() {
      const requestId = ++this.searchRequestId;
      this.searchError = null;
      const quickFilters = this.activeQuickFilters.map((id) =>
        QUICK_FILTERS.find((f) => f.id === id),
      );
      if (!this.appliedQuery && !quickFilters.length) {
        this.isSearching = false;
        this.resultSummary = null;
        this.$emit("update:result-keys", null);
        return;
      }

      // A custom filter is written for one type's properties, so only that type is searched.
      const types = this.appliedQuery
        ? this.config.types.filter((t) => t.id === this.appliedQuery.typeId)
        : this.config.types;
      const filters = [this.appliedQuery?.filter, ...quickFilters.map((f) => f.filter?.())];
      const params = Object.assign(
        {
          filter: filters
            .filter(Boolean)
            .map((f) => `(${f})`)
            .join(" AND "),
        },
        ...quickFilters.map((f) => f.params),
      );

      this.isSearching = true;
      try {
        const results = await Promise.all(
          types.map((t) => runQueryAllPages(t.id, params, MAX_RESULTS)),
        );
        if (requestId !== this.searchRequestId) return;
        this.resultSummary = this.summarize(types, results);
        this.$emit("update:result-keys", new Set(results.flatMap((r) => r.items.map(rowKey))));
      } catch (error) {
        if (requestId !== this.searchRequestId) return;
        this.searchError =
          error instanceof TypeError && error.message === "Failed to fetch"
            ? "Cannot reach the server. Check your connection."
            : error.message || "Search failed. Please try again.";
      } finally {
        if (requestId === this.searchRequestId) this.isSearching = false;
      }
    },
    // The chip of the custom filter, naming the searched type when the table holds several and
    // saying when not every match could be shown.
    summarize(types, results) {
      if (!this.appliedQuery) return null;
      let summary = this.appliedQuery.filter;
      if (this.config.types.length > 1) summary = `${types[0].label}: ${summary}`;
      const [{ items, total }] = results;
      return total > items.length ? `${summary} (first ${items.length} of ${total})` : summary;
    },
  },
};
</script>
