<template>
  <span class="metadata-field" @contextmenu.prevent="openMenu">
    <input
      v-if="editing"
      ref="input"
      v-model="draft"
      class="form-control form-control-sm"
      @keyup.enter="commit"
      @keyup.esc="editing = false"
      @blur="commit"
    />
    <template v-else>
      <span class="value" :class="{ empty: isEmpty }">{{ shown }}</span>
      <span class="source" :class="entry.source" :title="explanation">{{ badge }}</span>
    </template>

    <!-- Right-click menu. The options are whatever the block says it can offer,
         so a source with nothing to give never appears. -->
    <ul v-if="menuOpen" ref="menu" class="dropdown-menu show" :style="menuPosition">
      <li>
        <button class="dropdown-item" @click="startEditing">Override…</button>
      </li>
      <li v-for="(value, source) in offers" :key="source">
        <button class="dropdown-item" @click="bind(source)">
          Use {{ source }} value <span class="text-muted">({{ format(value) }})</span>
        </button>
      </li>
      <li><hr class="dropdown-divider" /></li>
      <li>
        <button class="dropdown-item" @click="clear">Set to empty</button>
      </li>
      <li v-if="entry.bound">
        <button class="dropdown-item" @click="bind('auto')">Choose automatically</button>
      </li>
    </ul>
  </span>
</template>

<script>
import { updateBlockFromServer } from "@/server_fetch_utils.js";
import store from "@/store/index.js";

export default {
  props: {
    item_id: { type: String, required: true },
    block_id: { type: String, required: true },
    field: { type: String, required: true },
    // As served in `metadata_fields`: the value, where it came from, whether that
    // was chosen or merely landed on, and what the other sources have to offer.
    entry: { type: Object, required: true },
  },
  data() {
    return { menuOpen: false, menuPosition: {}, editing: false, draft: "" };
  },
  computed: {
    isEmpty() {
      return this.entry.value === null || this.entry.value === undefined;
    },
    shown() {
      return this.isEmpty ? "—" : this.format(this.entry.value);
    },
    badge() {
      if (this.entry.source === "user") return this.entry.bound ? "edited" : "";
      return this.entry.source ?? "";
    },
    explanation() {
      if (this.entry.source === "user") {
        return this.isEmpty
          ? "Set to empty by hand; it will not be filled in from a file again"
          : "Entered by hand; nothing will overwrite it";
      }
      if (!this.entry.source) return "No source has a value for this";
      const how = this.entry.bound ? "Taken from" : "Read from";
      return `${how} the ${this.entry.source}, and follows it if it changes`;
    },
    // A source is only worth offering if it has something to offer and is not
    // already the one in use.
    offers() {
      const available = this.entry.available ?? {};
      return Object.fromEntries(
        Object.entries(available).filter(
          ([source, value]) =>
            value !== null && value !== undefined && source !== this.entry.source,
        ),
      );
    },
  },
  mounted() {
    document.addEventListener("click", this.closeMenu);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.closeMenu);
  },
  methods: {
    format(value) {
      return Array.isArray(value) ? value.join(", ") : String(value);
    },
    openMenu(event) {
      this.menuPosition = { top: `${event.offsetY}px`, left: `${event.offsetX}px` };
      this.menuOpen = true;
    },
    closeMenu() {
      this.menuOpen = false;
    },
    startEditing() {
      this.draft = this.isEmpty ? "" : this.format(this.entry.value);
      this.editing = true;
      this.menuOpen = false;
      this.$nextTick(() => this.$refs.input?.focus());
    },
    commit() {
      if (!this.editing) return;
      this.editing = false;
      const value = this.draft.trim();
      // An emptied box is a decision that this field has no good value, which is
      // why it is sent as a value of the user's rather than as no binding at all.
      this.send("user", value === "" ? null : value);
    },
    clear() {
      this.menuOpen = false;
      this.send("user", null);
    },
    bind(source) {
      this.menuOpen = false;
      this.send(source, null);
    },
    send(source, value) {
      const block = store.state.all_item_data[this.item_id]?.blocks_obj?.[this.block_id];
      updateBlockFromServer(this.item_id, this.block_id, block, {
        event_name: "set_metadata_source",
        field: this.field,
        source,
        value,
      }).catch((error) => console.error("Could not set the metadata source:", error));
    },
  },
};
</script>

<style scoped>
.metadata-field {
  position: relative;
  display: inline-flex;
  align-items: baseline;
  gap: 0.4rem;
  cursor: context-menu;
}

.value.empty {
  color: #adb5bd;
}

/* The provenance sits beside the value rather than replacing it: quiet enough to
   ignore while reading the numbers, there when you look for it. */
.source {
  font-size: 0.7rem;
  text-transform: lowercase;
  color: #adb5bd;
  border-bottom: 1px dotted currentColor;
  cursor: help;
}

/* A value somebody typed is the one worth being able to pick out. */
.source.user {
  color: #b8860b;
  font-style: italic;
}

.dropdown-menu {
  position: absolute;
  z-index: 1000;
}
</style>
