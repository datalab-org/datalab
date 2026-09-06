<template>
  <div v-if="hasMetadata" class="metadata-viewer">
    <div class="metadata-header">
      <span class="metadata-title">Metadata</span>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary copy-button"
        :aria-label="copied ? 'Metadata copied' : 'Copy metadata as JSON'"
        @click="copyAsJson"
      >
        <font-awesome-icon :icon="copied ? 'check' : 'copy'" fixed-width />
        {{ copied ? "Copied" : "Copy JSON" }}
      </button>
    </div>

    <dl class="metadata-list">
      <template v-for="(value, key) in displayedMetadata" :key="key">
        <dt :title="String(key)">{{ formatLabel(key) }}</dt>
        <dd>
          <!-- A field the block tracks the provenance of is editable in place and
               says where it came from; the rest are plain values. -->
          <MetadataField
            v-if="fields[key]"
            :item_id="item_id"
            :block_id="block_id"
            :field="String(key)"
            :entry="fields[key]"
            :source-labels="sourceLabels"
          />
          <details v-else-if="isExpandable(value)" class="value-details">
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
import MetadataField from "@/components/MetadataField";

// Values longer than this are collapsed behind a <details> rather than being
// allowed to dominate what is usually a narrow column beside a plot.
const INLINE_LENGTH_LIMIT = 80;

export default {
  components: {
    MetadataField,
  },
  props: {
    metadata: {
      type: Object,
      default: () => ({}),
    },
    // `metadata_fields` as the block serves it: the entries whose provenance is
    // known, keyed the same as `metadata`. Anything not in here renders as before.
    fields: {
      type: Object,
      default: () => ({}),
    },
    sourceLabels: {
      type: Object,
      default: () => ({}),
    },
    item_id: {
      type: String,
      default: null,
    },
    block_id: {
      type: String,
      default: null,
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
      copied: false,
      copyResetTimeout: null,
    };
  },
  computed: {
    displayedMetadata() {
      const values = this.metadata || {};

      // `fields` names every tracked field in the order the block declares them,
      // empty ones included, while `metadata` carries only those with a value.
      // Taking the order from `fields` is what stops a field moving down the list
      // the moment it is emptied and back up again when it is filled in.
      const keys = [...new Set([...Object.keys(this.fields), ...Object.keys(values)])];

      const filtered = {};
      for (const key of keys) {
        if (this.excludeKeys.includes(key)) continue;

        const value = values[key] ?? null;
        // An empty tracked field stays: it is exactly the one somebody needs to
        // reach in order to give it a value. An empty untracked one has nothing
        // to offer and is left out, as it always was.
        if (value === null && !(key in this.fields)) continue;

        filtered[key] = value;
      }
      return filtered;
    },
    hasMetadata() {
      return Object.keys(this.displayedMetadata).length > 0;
    },
  },
  beforeUnmount() {
    clearTimeout(this.copyResetTimeout);
  },
  methods: {
    formatLabel(key) {
      if (this.labels[key]) {
        return this.labels[key];
      }

      return (
        key
          .replace(/_/g, " ")
          // Split camelCase only at a lowercase/digit -> uppercase boundary, so
          // that unit acronyms such as `MHz` or `ppm` survive intact.
          .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
          .trim()
          .replace(/^\w/, (c) => c.toUpperCase())
      );
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
    async copyAsJson() {
      try {
        await navigator.clipboard.writeText(JSON.stringify(this.displayedMetadata, null, 2));
        this.copied = true;
        clearTimeout(this.copyResetTimeout);
        this.copyResetTimeout = setTimeout(() => {
          this.copied = false;
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
