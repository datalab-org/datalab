<template>
  <div v-if="hasComputed || hasMetadata" class="metadata-viewer">
    <div v-if="hasComputed" class="metadata-header">
      <span class="metadata-title">Computed</span>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary copy-button"
        :aria-label="copiedComputed ? 'Computed copied' : 'Copy computed data as JSON'"
        @click="copyAsJson(displayedComputed, 'copiedComputed')"
      >
        <font-awesome-icon :icon="copiedComputed ? 'check' : 'copy'" fixed-width />
        {{ copiedComputed ? "Copied" : "Copy JSON" }}
      </button>
    </div>

    <div v-if="hasComputed" class="metadata-list computed-list">
      <template v-for="section in computedSections" :key="section.key">
        <div v-if="section.title" class="computed-section-title" :title="section.key">
          {{ section.title }}
        </div>
        <dl class="mb-0">
          <template v-for="(value, key) in section.fields" :key="key">
            <dt :title="String(key)">{{ formatLabel(key) }}</dt>
            <dd>
              <details v-if="isExpandable(value)" class="value-details">
                <summary>{{ summaryFor(value) }}</summary>
                <pre class="value-json">{{ prettyPrint(value) }}</pre>
              </details>
              <span v-else class="value">{{ formatComputedValue(value) }}</span>
            </dd>
          </template>
        </dl>
      </template>
    </div>
    <div v-if="hasMetadata" class="metadata-header">
      <span class="metadata-title">Metadata</span>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary copy-button"
        :aria-label="copiedMetadata ? 'Metadata copied' : 'Copy metadata as JSON'"
        @click="copyAsJson(displayedMetadata, 'copiedMetadata')"
      >
        <font-awesome-icon :icon="copiedMetadata ? 'check' : 'copy'" fixed-width />
        {{ copiedMetadata ? "Copied" : "Copy JSON" }}
      </button>
    </div>

    <dl v-if="hasMetadata" class="metadata-list">
      <template v-for="(value, key) in displayedMetadata" :key="key">
        <dt :title="String(key)">{{ formatLabel(key) }}</dt>
        <dd>
          <details v-if="isExpandable(value)" class="value-details">
            <summary>{{ summaryFor(value) }}</summary>
            <pre class="value-json">{{ prettyPrint(value) }}</pre>
          </details>
          <span v-else class="value">{{ formatValue(value) }}</span>
        </dd>
      </template>
    </dl>
  </div>
</template>

<script>
// Values longer than this are collapsed behind a <details> rather than being
// allowed to dominate what is usually a narrow column beside a plot.
const INLINE_LENGTH_LIMIT = 80;

export default {
  props: {
    metadata: {
      type: Object,
      default: () => ({}),
    },
    computedData: {
      type: Object,
      default: () => ({}),
    },
    labels: {
      type: Object,
      default: () => ({}),
    },
    excludeKeys: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      copiedMetadata: false,
      copiedComputed: false,
      copyResetTimeout: null,
    };
  },
  computed: {
    displayedMetadata() {
      return this.filterFields(this.metadata);
    },
    displayedComputed() {
      return this.filterFields(this.computedData);
    },
    hasMetadata() {
      return Object.keys(this.displayedMetadata).length > 0;
    },
    hasComputed() {
      return Object.keys(this.displayedComputed).length > 0;
    },
    /**
     * Group computed fields for display: top-level scalars form an untitled
     * section, and each nested object (e.g. a plugin's namespaced results such
     * as `fast_metrics`) becomes its own titled section with its null fields
     * omitted.
     */
    computedSections() {
      const ungrouped = {};
      const sections = [];
      for (const [key, value] of Object.entries(this.displayedComputed)) {
        if (this.isPlainObject(value)) {
          const fields = this.filterFields(value);
          if (Object.keys(fields).length > 0) {
            sections.push({ key, title: this.formatLabel(key), fields });
          }
        } else {
          ungrouped[key] = value;
        }
      }
      if (Object.keys(ungrouped).length > 0) {
        sections.unshift({ key: "__ungrouped__", title: null, fields: ungrouped });
      }
      return sections;
    },
  },
  beforeUnmount() {
    clearTimeout(this.copyResetTimeout);
  },
  methods: {
    filterFields(dct) {
      if (!dct) return {};

      const filtered = {};
      for (const [key, value] of Object.entries(dct)) {
        if (!this.excludeKeys.includes(key) && value !== null && value !== undefined) {
          filtered[key] = value;
        }
      }
      return filtered;
    },
    formatLabel(key) {
      if (this.labels[key]) {
        return this.labels[key];
      }

      // snake_case keys are already word-separated, and may embed mixed-case
      // units (e.g. `capacity_mAh`) that camelCase splitting would mangle.
      const label = key.includes("_")
        ? key.replace(/_/g, " ")
        : // Split camelCase only at a lowercase/digit -> uppercase boundary, so
          // that unit acronyms such as `MHz` or `ppm` survive intact.
          key.replace(/([a-z0-9])([A-Z])/g, "$1 $2");

      return label.trim().replace(/^\w/, (c) => c.toUpperCase());
    },
    isExpandable(value) {
      if (value !== null && typeof value === "object" && !Array.isArray(value)) {
        return true;
      }
      return this.formatValue(value).length > INLINE_LENGTH_LIMIT;
    },
    summaryFor(value) {
      if (Array.isArray(value)) {
        return `${value.length} item${value.length === 1 ? "" : "s"}`;
      }
      if (value !== null && typeof value === "object") {
        const n = Object.keys(value).length;
        return `${n} field${n === 1 ? "" : "s"}`;
      }
      return `${this.formatValue(value).slice(0, INLINE_LENGTH_LIMIT)}…`;
    },
    prettyPrint(value) {
      if (typeof value === "object") {
        return JSON.stringify(value, null, 2);
      }
      return String(value);
    },
    isPlainObject(value) {
      return value !== null && typeof value === "object" && !Array.isArray(value);
    },
    /**
     * As `formatValue`, but rounds non-integer numbers to a readable number of
     * significant figures (the copied JSON keeps full precision).
     */
    formatComputedValue(value) {
      if (typeof value === "number" && !Number.isInteger(value)) {
        return String(Number(value.toPrecision(5)));
      }
      return this.formatValue(value);
    },
    formatValue(value) {
      if (value === null || value === undefined) {
        return "";
      }
      if (Array.isArray(value)) {
        return value.join(", ");
      }
      if (typeof value === "object") {
        return JSON.stringify(value);
      }
      return String(value);
    },
    /**
     * Copy an object to the clipboard as pretty-printed JSON, and briefly set
     * the given data flag so the corresponding button shows "Copied".
     *
     * @param {Object} dct - The object to serialise and copy.
     * @param {string} flag - Name of the boolean data property to toggle
     *   (e.g. `"copiedMetadata"` or `"copiedComputed"`).
     */
    async copyAsJson(dct, flag) {
      try {
        await navigator.clipboard.writeText(JSON.stringify(dct, null, 2));
        this[flag] = true;
        clearTimeout(this.copyResetTimeout);
        this.copyResetTimeout = setTimeout(() => {
          this[flag] = false;
        }, 2000);
      } catch (error) {
        console.error("Could not copy metadata to the clipboard:", error);
      }
    },
  },
};
</script>

<style scoped>
/* A light container so the metadata reads as a distinct panel beside the plot,
   without competing with it. The inner JSON blocks use a grey fill, so this
   stays white to keep them legible against it. */
.metadata-viewer {
  padding: 0.75rem 1rem;
  background-color: #fff;
  border: 1px solid #e9ecef;
  border-radius: 0.35rem;
}

.metadata-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #f1f3f5;
}

.metadata-title {
  font-weight: 600;
  color: #454545;
}

.copy-button {
  white-space: nowrap;
}

/* A definition list rather than a table: labels sit above their values, which
   keeps long values readable in the narrow column beside a plot. */
.metadata-list {
  margin-bottom: 0;
  /* Blocks can expose hundreds of fields (e.g. raw acquisition parameters), so
     scroll the list rather than letting the panel run far past the plot. The
     header sits outside this box, keeping the copy button always reachable. */
  max-height: 30rem;
  overflow-y: auto;
  /* Keeps values clear of the scrollbar when one appears. */
  padding-right: 0.35rem;
}

.computed-list {
  margin-bottom: 0.75rem;
}

.computed-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #454545;
  margin: 0.25rem 0 0.4rem;
}

.metadata-list dt {
  font-size: 0.8rem;
  font-weight: 500;
  color: #6c757d;
  margin-top: 0.6rem;
}

.metadata-list dt:first-child {
  margin-top: 0;
}

.metadata-list dd {
  margin-bottom: 0;
  /* Long unbroken values (paths, encoded strings) must not force the column
     wider than its container. */
  overflow-wrap: anywhere;
}

.value-details summary {
  cursor: pointer;
  color: #6c757d;
}

.value-details summary:hover {
  color: cornflowerblue;
}

.value-json {
  margin: 0.35rem 0 0;
  padding: 0.5rem;
  max-height: 16rem;
  overflow: auto;
  font-size: 0.78rem;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
}
</style>
