<template>
  <div class="location-input" @focusout="onFocusOut">
    <div
      v-if="!isEditing"
      :id="inputId || undefined"
      class="form-control location-display"
      :class="{ 'location-display--readonly': readonly }"
      :role="readonly ? undefined : 'button'"
      :aria-labelledby="labelledBy || undefined"
      :tabindex="readonly ? -1 : 0"
      @click="startEditing"
      @keydown.enter.prevent="startEditing"
    >
      <span v-if="modelValue">{{ modelValue }}</span>
      <span v-else class="text-muted placeholder-text">Add location…</span>
    </div>
    <div
      v-else
      class="location-inline d-flex align-items-center flex-wrap"
      role="group"
      :aria-labelledby="labelledBy || undefined"
    >
      <template v-for="(segment, i) in editableSegments" :key="i">
        <font-awesome-icon v-if="i > 0" icon="chevron-right" class="location-chevron" />
        <div class="location-segment-wrap">
          <AutoComplete
            :model-value="segment"
            :suggestions="filteredSuggestions[i] || []"
            :aria-label="`Location level ${i + 1}`"
            complete-on-focus
            input-class="form-control location-segment-input"
            @option-select="(e) => onOptionSelect(i, e)"
            @complete="(e) => onComplete(e, i)"
            @update:model-value="(val) => updateSegment(i, val)"
          />
          <button
            v-if="editableSegments.length > 1"
            type="button"
            class="remove-btn"
            :aria-label="`Remove location level ${i + 1}`"
            @click="removeSegment(i)"
          >
            <font-awesome-icon icon="times" />
          </button>
        </div>
      </template>
      <button type="button" class="add-btn" aria-label="Add location level" @click="addSegment">
        +
      </button>
    </div>
  </div>
</template>

<script>
import AutoComplete from "primevue/autocomplete";

export default {
  components: { AutoComplete },
  props: {
    modelValue: { type: String, default: "" },
    // The `nested_locations` tree from GET /locations: each key is a location
    // segment mapping to an object of its child segments.
    hierarchy: { type: Object, default: () => ({}) },
    readonly: { type: Boolean, default: false },
    inputId: { type: String, default: "" },
    // id of the external <label> naming this control
    labelledBy: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      editableSegments: this.parseSegments(this.modelValue),
      filteredSuggestions: {},
      isEditing: false,
    };
  },
  watch: {
    modelValue(val) {
      if (val !== this.buildValue(this.editableSegments)) {
        this.editableSegments = this.parseSegments(val);
      }
    },
  },
  methods: {
    parseSegments(val) {
      if (!val) return [""];
      const parts = val
        .split(" > ")
        .map((s) => s.trim())
        .filter(Boolean);
      return parts.length ? parts : [""];
    },
    buildValue(segs) {
      return segs.filter(Boolean).join(" > ");
    },
    startEditing() {
      if (this.readonly) return;
      this.isEditing = true;
      this.focusSegment(0);
    },
    focusSegment(index) {
      this.$nextTick(() => {
        const inputs = this.$el.querySelectorAll("input");
        const input = inputs[index] || inputs[inputs.length - 1];
        if (input) input.focus();
      });
    },
    onFocusOut() {
      setTimeout(() => {
        if (this.$el && !this.$el.contains(document.activeElement)) {
          this.isEditing = false;
        }
      }, 200);
    },
    updateSegment(index, val) {
      const segs = this.editableSegments.map((s, i) => (i === index ? val : s));
      this.editableSegments = segs;
      this.$emit("update:modelValue", this.buildValue(segs));
    },
    addSegment() {
      this.editableSegments = [...this.editableSegments, ""];
      // focusing the new segment surfaces its options straight away
      this.focusSegment(this.editableSegments.length - 1);
    },
    removeSegment(index) {
      const segs = this.editableSegments.filter((_, i) => i !== index);
      this.editableSegments = segs.length ? segs : [""];
      this.$emit("update:modelValue", this.buildValue(this.editableSegments));
    },
    nodeAt(segments, level) {
      // Walk down the hierarchy along the given segments, returning the node
      // reached, or null when the path does not exist in the hierarchy.
      let node = this.hierarchy;
      for (const segment of segments.slice(0, level)) {
        const key = (segment || "").trim();
        if (!key || !node[key]) return null;
        node = node[key];
      }
      return node;
    },
    getSegmentOptions(level) {
      // Each level only ever offers the children of the path above it.
      return Object.keys(this.nodeAt(this.editableSegments, level) || {}).sort();
    },
    onOptionSelect(level, event) {
      // Picking a location steps straight into it: open the next segment so its
      // own options are listed, without having to reach for the '+' button.
      const selected = event?.value ?? this.editableSegments[level];
      const segments = this.editableSegments.map((s, i) => (i === level ? selected : s));

      // Deeper segments survive only while they still exist under the location
      // just picked, so switching branch cannot leave a stale child behind;
      // re-picking the same one keeps what was already there.
      const kept = segments.slice(0, level + 1);
      let node = this.nodeAt(segments, level + 1) || {};
      for (const segment of segments.slice(level + 1)) {
        const key = (segment || "").trim();
        if (!key || !node[key]) break;
        kept.push(segment);
        node = node[key];
      }

      // A leaf has nothing to step into, so focus simply stays put (which also
      // keeps it inside the component, see `onFocusOut`).
      const hasChildren = Object.keys(this.nodeAt(segments, level + 1) || {}).length > 0;
      if (hasChildren && kept.length === level + 1) {
        kept.push("");
      }
      this.editableSegments = kept;
      this.$emit("update:modelValue", this.buildValue(kept));

      // PrimeVue restores focus to the segment just picked from a `setTimeout`
      // queued right after this event, so queue ours behind it rather than
      // racing it: the `$nextTick` defers scheduling until that timeout exists.
      const target = hasChildren ? level + 1 : level;
      this.$nextTick(() => setTimeout(() => this.focusSegment(target)));
    },
    setFilteredSuggestions(level, options) {
      // Only ever keep one level's list: PrimeVue leaves the previous segment's
      // overlay open when focus moves on, which would otherwise stack the
      // options of two levels on top of each other.
      this.filteredSuggestions = { [level]: options };
    },
    onComplete(event, level) {
      // PrimeVue refocuses an input after one of its options is picked, which
      // re-runs the query for a segment the user has already moved on from.
      // Ignore those so a stale level cannot reopen over the focused one.
      const input = this.$el.querySelectorAll("input")[level];
      if (input && document.activeElement !== input) {
        return;
      }
      // `complete-on-focus` runs this with an empty query as soon as a segment is
      // focused, so the whole branch is offered for browsing before anything is
      // typed; typing then narrows it.
      const query = (event.query || "").toLowerCase();
      const options = this.getSegmentOptions(level);
      this.setFilteredSuggestions(
        level,
        query ? options.filter((s) => s.toLowerCase().includes(query)) : options,
      );
    },
  },
};
</script>

<style scoped>
.location-display {
  cursor: pointer;
  min-height: 38px;
  display: flex;
  align-items: center;
}
.location-display--readonly {
  cursor: default;
  background-color: #e9ecef;
}
.placeholder-text {
  font-style: italic;
}
.location-inline {
  gap: 4px;
}
.location-chevron {
  color: var(--color-text-secondary, #64748b);
  font-size: 0.8rem;
  margin: 0 4px;
  flex-shrink: 0;
}
.location-segment-wrap {
  position: relative;
  display: inline-flex;
}
.remove-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #94a3b8;
  padding: 0;
  font-size: 0.7rem;
  cursor: pointer;
  z-index: 1;
  line-height: 1;
}
.remove-btn:hover {
  color: #dc3545;
}
.add-btn {
  background: none;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 4px;
  color: var(--color-text-secondary, #64748b);
  padding: 0 10px;
  font-size: 1rem;
  cursor: pointer;
  height: 38px;
  line-height: 1;
}
.add-btn:hover {
  background: var(--color-accent-light, #eef2ff);
  border-color: var(--color-accent, #6366f1);
  color: var(--color-accent, #6366f1);
}
:deep(.p-autocomplete) {
  display: inline-flex;
  width: 160px;
}
:deep(.location-segment-input) {
  padding-right: 28px;
  width: 100%;
}
</style>
