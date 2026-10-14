<template>
  <Modal v-model="isOpen" :is-large="true">
    <template #header>Advanced Search</template>

    <template #body>
      <div :key="typeRadiosKey" class="form-group">
        <label class="font-weight-bold d-block">Item type</label>
        <div v-for="t in types" :key="t.id" class="form-check form-check-inline">
          <input
            :id="`adv-qt-${t.id}`"
            type="radio"
            :value="t.id"
            :checked="(pendingTypeChange?.typeId ?? selectedType) === t.id"
            class="form-check-input"
            @change="onTypeChange(t.id)"
          />
          <label :for="`adv-qt-${t.id}`" class="form-check-label">{{ t.label }}</label>
        </div>
        <small v-if="typeChangeError" class="form-text text-danger">{{ typeChangeError }}</small>
      </div>

      <div v-if="pendingTypeChange" class="alert alert-warning">
        {{ stalRulesCount }} condition(s) will be cleared when switching type.
        <div class="mt-2">
          <button type="button" class="btn btn-sm btn-warning mr-2" @click="confirmTypeChange">
            Confirm
          </button>
          <button type="button" class="btn btn-sm btn-secondary" @click="cancelTypeChange">
            Cancel
          </button>
        </div>
      </div>

      <div v-if="schemaLoading" class="text-muted">Loading fields…</div>
      <div v-else-if="schemaError" class="text-danger">{{ schemaError }}</div>

      <template v-else-if="schema">
        <fieldset :disabled="manualFilter !== null">
          <label class="font-weight-bold">Conditions</label>
          <QueryGroup
            :node="rootGroup"
            :fields="schema.fields"
            :max-depth="schema?.capabilities?.max_depth ?? 0"
            :current-depth="0"
            @update:node="rootGroup = $event"
          />
        </fieldset>

        <div class="form-group mt-3 mb-0">
          <label for="adv-optimade-filter" class="font-weight-bold">OPTIMADE filter</label>
          <textarea
            id="adv-optimade-filter"
            data-testid="optimade-filter-input"
            class="form-control text-monospace"
            rows="3"
            spellcheck="false"
            :value="effectiveFilter"
            placeholder='e.g. name CONTAINS "LFP" AND date >= "2026-01-01T00:00:00Z"'
            @input="manualFilter = $event.target.value"
          ></textarea>
          <small class="form-text text-muted">
            <template v-if="manualFilter !== null">
              Edited by hand, so the conditions above are not used.
              <a href="#" @click.prevent="manualFilter = null">Use the conditions instead</a>.
            </template>
            <template v-else>
              Built from the conditions above; edit it to write the filter by hand.
            </template>
            See the
            <a :href="OPTIMADE_FILTER_DOCS" target="_blank" rel="noopener">filter syntax</a>.
          </small>
        </div>
      </template>
    </template>

    <template #footer>
      <span v-if="queryError || previewError" class="text-danger small mr-auto">
        {{ queryError || previewError }}
      </span>
      <span v-else-if="previewLoading" class="text-muted small mr-auto">
        <font-awesome-icon icon="sync" spin class="mr-1" /> Counting…
      </span>
      <span v-else-if="previewCount !== null" class="text-muted small mr-auto">
        Found: {{ previewCount }}
      </span>
      <button type="button" class="btn btn-secondary" @click="isOpen = false">Cancel</button>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="queryLoading || pendingTypeChange !== null"
        :title="pendingTypeChange ? 'Confirm or cancel the change of item type first' : ''"
        @click="submitQuery"
      >
        <font-awesome-icon v-if="queryLoading" icon="sync" spin class="mr-1" />
        Search
      </button>
    </template>
  </Modal>
</template>

<script>
import { fetchQuerySchema, runQuery, runQueryAllPages } from "@/server_fetch_utils.js";
import Modal from "@/components/Modal.vue";
import QueryGroup from "@/components/QueryGroup.vue";
import { buildOptimadeFilter } from "@/utils/optimadeFilter.js";

const OPTIMADE_FILTER_DOCS =
  "https://www.optimade.org/specification/latest/#api-filtering-format-specification";

// At most this many results are loaded into the table.
const MAX_RESULTS = 2000;

export default {
  name: "AdvancedQueryBuilder",
  components: { Modal, QueryGroup },
  props: {
    // Types this search can query, as `{ id, label }`.
    types: { type: Array, required: true },
  },
  emits: ["query-results", "update:applied-summary"],
  data() {
    return {
      isOpen: false,
      selectedType: null,
      // Why the last switch of item type failed, if it did; the previous type stays selected.
      typeChangeError: null,
      // Bumped to re-render the type radios, so that a failed switch un-checks the new one.
      typeRadiosKey: 0,
      // Bumped by each schema request, so that only the latest one is applied.
      schemaRequestId: 0,
      pendingTypeChange: null,
      stalRulesCount: 0,
      schema: { capabilities: { max_depth: 0 }, fields: [] },
      schemaLoading: false,
      schemaError: null,
      rootGroup: this.emptyGroup(),
      queryLoading: false,
      queryError: null,
      appliedSummary: null,
      // Bumped to discard a search still running when it is cancelled or cleared.
      searchRequestId: 0,
      previewCount: null,
      previewLoading: false,
      previewTimer: null,
      previewError: null,
      previewRequestId: 0,
      // Filter typed by hand in the OPTIMADE textarea; null while it follows the conditions.
      manualFilter: null,
      OPTIMADE_FILTER_DOCS,
    };
  },
  computed: {
    // The filter built from the conditions ("" while they are incomplete), or the reason it
    // cannot be built, e.g. "abc" as the value of a number property.
    generatedFilterResult() {
      if (!this.schema || this.validateRules(this.rootGroup)) return { filter: "", error: null };
      try {
        return { filter: buildOptimadeFilter(this.rootGroup, this.schema.fields), error: null };
      } catch (e) {
        return { filter: "", error: e.message };
      }
    },
    generatedFilter() {
      return this.generatedFilterResult.filter;
    },
    effectiveFilter() {
      return this.manualFilter ?? this.generatedFilter;
    },
  },
  watch: {
    rootGroup: {
      deep: true,
      handler() {
        this.schedulePreview();
      },
    },
    selectedType() {
      this.schedulePreview();
    },
    manualFilter() {
      this.schedulePreview();
    },
    appliedSummary(newVal) {
      this.$emit("update:applied-summary", newVal);
    },
    isOpen(open) {
      // Closing the modal (Cancel, ×, backdrop) cancels a search that is still running.
      if (!open && this.queryLoading) this.cancelSearch();
    },
  },
  async mounted() {
    if (this.types.length) {
      this.selectedType = this.types[0].id;
      await this.loadSchema(this.selectedType);
    }
  },
  beforeUnmount() {
    clearTimeout(this.previewTimer);
  },
  methods: {
    open() {
      this.isOpen = true;
      // Retry loading the fields if that failed before, e.g. while the server was unreachable.
      if (this.schemaError && this.selectedType) this.loadSchema(this.selectedType);
    },

    emptyGroup() {
      return { kind: "group", combinator: "and", children: [] };
    },

    async fetchSchema(typeId) {
      const schema = await fetchQuerySchema(typeId);
      return { fields: schema.fields, capabilities: { max_depth: schema.max_depth } };
    },

    async loadSchema(typeId) {
      const requestId = ++this.schemaRequestId;
      this.schemaLoading = true;
      this.schemaError = null;
      try {
        const schema = await this.fetchSchema(typeId);
        if (requestId === this.schemaRequestId) this.schema = schema;
      } catch (e) {
        if (requestId === this.schemaRequestId) this.schemaError = e.message;
      } finally {
        if (requestId === this.schemaRequestId) this.schemaLoading = false;
      }
    },

    countStaleRules(node, validFieldIds) {
      if (node.kind === "rule") return validFieldIds.includes(node.field) ? 0 : 1;
      return (node.children || []).reduce(
        (sum, child) => sum + this.countStaleRules(child, validFieldIds),
        0,
      );
    },

    // The new type's schema is fetched before switching, so that on failure the current type,
    // its schema and the conditions all stay as they are.
    async onTypeChange(newTypeId) {
      const requestId = ++this.schemaRequestId;
      this.typeChangeError = null;
      this.pendingTypeChange = null;
      let newSchema;
      try {
        newSchema = await this.fetchSchema(newTypeId);
      } catch (e) {
        if (requestId !== this.schemaRequestId) return;
        this.typeChangeError = `Could not load the fields of this type: ${e.message}`;
        this.typeRadiosKey++;
        return;
      }
      // A later type change (or schema reload) was requested meanwhile and takes precedence.
      if (requestId !== this.schemaRequestId) return;
      const stale = this.countStaleRules(
        this.rootGroup,
        newSchema.fields.map((f) => f.id),
      );
      if (stale === 0) {
        this.switchType(newTypeId, newSchema);
        return;
      }
      this.stalRulesCount = stale;
      this.pendingTypeChange = { typeId: newTypeId, schema: newSchema };
    },

    switchType(typeId, schema) {
      this.selectedType = typeId;
      this.schema = schema;
      this.schemaError = null;
      this.schemaLoading = false;
    },

    confirmTypeChange() {
      const { typeId, schema } = this.pendingTypeChange;
      this.switchType(typeId, schema);
      this.rootGroup = this.emptyGroup();
      this.pendingTypeChange = null;
    },

    cancelTypeChange() {
      this.pendingTypeChange = null;
    },

    validateRules(node) {
      if (node.kind === "rule") {
        if (!node.field) return "Select a field for all rules.";
        if (!node.operator) return "Select an operator for all rules.";
        const field = this.schema?.fields.find((f) => f.id === node.field);
        const op = field?.operators.find((o) => o.id === node.operator);
        if (op?.value_required) {
          const v = node.value;
          const isEmpty =
            v === undefined ||
            v === null ||
            v === "" ||
            (Array.isArray(v) && v.filter(Boolean).length === 0);
          if (isEmpty) return `"${field?.label || node.field}": value is required.`;
        }
        return null;
      }
      if (node.kind === "group") {
        for (const child of node.children || []) {
          const err = this.validateRules(child);
          if (err) return err;
        }
      }
      return null;
    },

    // URL query parameters for the current search; `filter` is in the OPTIMADE filter language.
    // Results are not sorted here: the table sorts the rows it shows by its own columns.
    queryParams(extra = {}) {
      return { filter: this.effectiveFilter.trim(), ...extra };
    },

    schedulePreview() {
      clearTimeout(this.previewTimer);
      // The conditions changed, so an error about the previous ones no longer applies.
      this.queryError = null;
      this.previewError = this.manualFilter === null ? this.generatedFilterResult.error : null;
      if (!this.effectiveFilter.trim()) {
        this.previewCount = null;
        this.previewLoading = false;
        return;
      }
      this.previewLoading = true;
      this.previewTimer = setTimeout(() => this.fetchPreview(), 400);
    },

    async fetchPreview() {
      if (!this.selectedType || !this.schema || !this.effectiveFilter.trim()) {
        this.previewLoading = false;
        this.previewCount = null;
        return;
      }
      // Ignore responses to earlier previews that arrive after a newer one was requested.
      const requestId = ++this.previewRequestId;
      try {
        // limit=0 returns no items, only the number matching the filter.
        const result = await runQuery(this.selectedType, this.queryParams({ limit: 0 }));
        if (requestId !== this.previewRequestId) return;
        this.previewCount = `${result.total} item${result.total !== 1 ? "s" : ""}`;
      } catch (e) {
        if (requestId !== this.previewRequestId) return;
        this.previewCount = null;
        this.previewError = e.message;
      } finally {
        if (requestId === this.previewRequestId) this.previewLoading = false;
      }
    },

    async submitQuery() {
      this.queryError = null;
      const validationError =
        this.manualFilter === null &&
        (this.validateRules(this.rootGroup) || this.generatedFilterResult.error);
      if (validationError) {
        this.queryError = validationError;
        return;
      }
      const filter = this.effectiveFilter.trim();
      if (!filter) {
        // Nothing to search for: show the whole table again rather than only one type.
        this.clearFilters();
        this.isOpen = false;
        return;
      }
      const requestId = ++this.searchRequestId;
      this.queryLoading = true;
      try {
        const { items: allItems, total } = await runQueryAllPages(
          this.selectedType,
          this.queryParams(),
          MAX_RESULTS,
        );
        if (requestId !== this.searchRequestId) return;

        // Results only contain the searched type, so name it when the table holds several.
        const typeLabel = this.types.find((t) => t.id === this.selectedType)?.label;
        let summary = this.types.length > 1 ? `${typeLabel}: ${filter}` : filter;
        if (total > allItems.length) {
          summary += ` (first ${allItems.length} of ${total})`;
        }
        this.appliedSummary = summary;
        this.$emit("query-results", allItems);
        this.isOpen = false;
      } catch (e) {
        if (requestId !== this.searchRequestId) return;
        if (e instanceof TypeError && e.message === "Failed to fetch") {
          this.queryError = "Cannot reach the server. Check your connection.";
        } else {
          this.queryError = e.message || "Query failed. Please try again.";
        }
      } finally {
        if (requestId === this.searchRequestId) this.queryLoading = false;
      }
    },

    cancelSearch() {
      this.searchRequestId++;
      this.queryLoading = false;
    },

    clearFilters() {
      this.cancelSearch();
      this.rootGroup = this.emptyGroup();
      this.manualFilter = null;
      this.appliedSummary = null;
      this.previewCount = null;
      this.queryError = null;
      this.previewError = null;
      this.$emit("query-results", null);
    },
  },
};
</script>
