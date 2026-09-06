<template>
  <!-- A div rather than a span: the menu is a `ul`, which a span cannot contain. -->
  <div class="metadata-field" @click.stop="toggleMenu" @contextmenu.prevent.stop="openMenu">
    <!-- `click.stop` for the same reason as on the menu: saving or abandoning an
         edit must not fall through and open the menu behind it. -->
    <span v-if="editing" class="editor" @click.stop>
      <input
        ref="input"
        v-model="draft"
        class="form-control form-control-sm"
        @keyup.enter="commit"
        @keyup.esc="cancel"
        @blur="cancel"
      />
      <!-- `mousedown.prevent` so the input never loses focus, which would cancel
           the edit out from under the button being pressed. -->
      <button class="btn btn-sm btn-link" title="Save" @mousedown.prevent="commit">
        <font-awesome-icon icon="check" fixed-width />
      </button>
      <button class="btn btn-sm btn-link cancel" title="Cancel" @mousedown.prevent="cancel">
        <font-awesome-icon icon="times" fixed-width />
      </button>
    </span>
    <template v-else>
      <span class="value" :class="{ empty: isEmpty }">{{ shown }}</span>
      <span class="source" :class="entry.source" :title="explanation">{{ badge }}</span>
    </template>

    <!-- The options are whatever the block says it can offer, so a source with
         nothing to give never appears. -->
    <!-- `click.stop` so choosing an option does not bubble back to the field and
         reopen the menu that the option just closed. -->
    <ul v-if="menuOpen" class="dropdown-menu show" @click.stop>
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
      <li>
        <button class="dropdown-item text-muted" @click="closeMenu">Cancel</button>
      </li>
    </ul>
  </div>
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
    // What to call each source when explaining where a value came from: the name
    // of the file rather than "file".
    sourceLabels: { type: Object, default: () => ({}) },
  },
  data() {
    return { menuOpen: false, editing: false, draft: "" };
  },
  computed: {
    isEmpty() {
      return this.entry.value === null || this.entry.value === undefined;
    },
    shown() {
      return this.isEmpty ? "—" : this.format(this.entry.value);
    },
    badge() {
      if (this.entry.source === "user") return this.entry.bound ? "user supplied" : "";
      return this.entry.source ?? "";
    },
    // Who made a choice and when, where anyone is recorded. A binding made outside
    // a request -- by a script, or before this was tracked -- has neither.
    attribution() {
      const who = this.entry.set_by_name ? ` by ${this.entry.set_by_name}` : "";
      const when = this.entry.set_at ? ` on ${new Date(this.entry.set_at).toLocaleString()}` : "";
      return who + when;
    },
    explanation() {
      if (this.entry.source === "user") {
        const what = this.isEmpty ? "Value set to blank" : "Value overwritten";
        return `${what}${this.attribution || " by user"}`;
      }
      if (!this.entry.source) return "No source has a value for this";

      const supplied = `Supplied by ${this.sourceLabels[this.entry.source] ?? this.entry.source}`;
      // Only worth saying who chose it where somebody did; otherwise the block
      // worked it out and there is nobody to name.
      return this.entry.bound && this.attribution
        ? `${supplied}, chosen${this.attribution}`
        : supplied;
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
    openMenu() {
      if (!this.editing) this.menuOpen = true;
    },
    toggleMenu() {
      // Nothing to choose while a value is being typed; the editor has its own
      // save and cancel.
      if (this.editing) return;
      this.menuOpen = !this.menuOpen;
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
    cancel() {
      this.editing = false;
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
  cursor: pointer;
}

.editor {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
}

.editor .btn-link {
  padding: 0 0.2rem;
  color: #6c757d;
}

.editor .btn-link:hover {
  color: cornflowerblue;
}

.editor .cancel:hover {
  color: #c92a2a;
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
}

/* A value somebody typed is the one worth being able to pick out. Deliberately
   not in the yellow the rest of datalab uses for unsaved changes: this says where
   a value came from, not that anything needs doing about it. */
.source.user {
  color: #4a6fa5;
  font-style: italic;
}

/* Below the value rather than at the pointer, so it lands in the same place
   however the menu was opened. */
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
}
</style>
