<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="tagOptions"
    label="name"
    multiple
    :filterable="false"
    placeholder="type to search for a tag..."
    v-bind="$attrs"
    @search="debouncedAsyncSearch"
  >
    <template #no-options="{ searching }">
      <span v-if="isSearchFetchError" class="search-error">
        Couldn't reach the server to search tags.
      </span>
      <span v-else-if="searching"> No matching tags. </span>
      <span v-else class="empty-search"> Type to search for a tag... </span>
    </template>
    <template #option="{ name, color, description, scope }">
      <!-- d-flex fills the option row so the description tooltip triggers anywhere on it. -->
      <span class="d-flex align-items-center" :title="description || name">
        <span v-if="color" class="color-swatch" :style="{ backgroundColor: color }"></span>
        <span>{{ name }}</span>
        <span
          class="badge badge-pill ml-auto"
          :class="scope === 'user' ? 'badge-info' : 'badge-secondary'"
          data-testid="tag-scope-badge"
        >
          <font-awesome-icon v-if="scope === 'user'" :icon="['fas', 'user']" class="mr-1" />
          {{ scope === "user" ? "personal" : "global" }}
        </span>
      </span>
    </template>
    <template #selected-option="{ name, color, description, scope }">
      <span v-if="color" class="color-swatch" :style="{ backgroundColor: color }"></span>
      <font-awesome-icon
        v-if="scope === 'user'"
        :icon="['fas', 'user']"
        class="mr-1"
        title="Personal tag"
      />
      <span :title="description || name">{{ name }}</span>
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import { searchTags } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";

export default {
  components: {
    vSelect,
  },
  props: {
    // Each entry is a reference object
    // `{ type: "tags", immutable_id, name, color?, description? }`, matching the
    // backend `tags` field (color/description are display fields, re-resolved on read).
    modelValue: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      debounceTimeout: null,
      tags: [],
      // Cache of search results keyed by immutable_id, used to recover display-only
      // details (e.g. color) for tags whose stored reference is stripped to id+name.
      tagDetailsById: {},
      isSearchFetchError: false,
    };
  },
  computed: {
    // Map between the backend reference form and the object form vue-select works
    // with internally (always `{ name, ... }`).
    value: {
      get() {
        return (this.modelValue || []).map((tag) => {
          // Display fields come from the backend-resolved item tag, falling back to
          // the search cache (e.g. for a tag just picked, before a re-resolve).
          const cached = this.tagDetailsById[tag.immutable_id] || {};
          return {
            name: tag.name,
            immutable_id: tag.immutable_id,
            type: "tags",
            color: tag.color ?? cached.color ?? null,
            description: tag.description ?? cached.description ?? null,
            // `scope` is display-only.
            scope: tag.scope ?? cached.scope ?? null,
          };
        });
      },
      set(newValue) {
        // Preserve display fields (color/description) on the stored reference so
        // they survive the edit<->display toggle without a re-fetch. They are
        // re-resolved on every read, so this is harmless denormalisation (like `name`).
        const mapped = (newValue || []).map((tag) => {
          const ref = { type: "tags", immutable_id: tag.immutable_id, name: tag.name };
          if (tag.color) {
            ref.color = tag.color;
          }
          if (tag.description) {
            ref.description = tag.description;
          }
          // Keep `scope` so a just-added personal tag keeps its marker across the
          // edit<->display toggle. Like color/description it is display-only and
          // is stripped by the server on save (only {type, immutable_id} persists).
          if (tag.scope) {
            ref.scope = tag.scope;
          }
          return ref;
        });
        this.$emit("update:modelValue", mapped);
      },
    },
    tagOptions() {
      // Hide tags that are already selected (matched by id).
      const selectedIds = new Set(this.value.map((tag) => tag.immutable_id).filter((id) => id));
      return this.tags.filter((tag) => !selectedIds.has(tag.immutable_id));
    },
  },
  beforeUnmount() {
    clearTimeout(this.debounceTimeout);
  },
  methods: {
    async debouncedAsyncSearch(query, loading) {
      loading(true);
      clearTimeout(this.debounceTimeout); // reset the timer
      // The backend rejects an empty query with a 400, so skip the request entirely
      // (e.g. when the user clears the input) rather than surfacing a false error.
      if (!query.trim()) {
        this.tags = [];
        this.isSearchFetchError = false;
        loading(false);
        return;
      }
      this.debounceTimeout = setTimeout(async () => {
        this.isSearchFetchError = false; // clear stale error from a previous search
        await searchTags(query, 100)
          .then((tags) => {
            this.tags = tags;
            tags.forEach((tag) => {
              if (tag.immutable_id) {
                this.tagDetailsById[tag.immutable_id] = tag;
              }
            });
          })
          .catch((error) => {
            console.error("Fetch error");
            console.error(error);
            this.tags = []; // don't show stale results alongside the error message
            this.isSearchFetchError = true;
          });
        loading(false);
      }, debounceTime);
    },
  },
};
</script>

<style scoped>
.color-swatch {
  display: inline-block;
  width: 0.7em;
  height: 0.7em;
  border-radius: 50%;
  margin-right: 0.3em;
  vertical-align: middle;
  border: 1px solid rgba(0, 0, 0, 0.25);
}
.search-error {
  color: #b00020;
}
</style>
