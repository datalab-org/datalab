<template>
  <div class="tag-list d-flex flex-wrap align-items-center">
    <TagBadge v-for="(tag, index) in visibleTags" :key="tagKey(tag, index)" :tag="tag" />
    <button
      v-if="hiddenTagCount"
      type="button"
      class="more-tags-trigger d-inline-flex align-items-center border-0 bg-transparent p-0"
      aria-label="Show all tags"
      @click.stop="togglePopover"
    >
      <BaseIconCounter
        :count="hiddenTagCount"
        :max-display="hiddenTagCount"
        :hover-text="counterHoverText"
        prefix="+"
      />
    </button>
    <span v-if="!tags || tags.length === 0" class="text-muted small">No tags</span>
    <Popover
      v-if="hiddenTagCount"
      ref="tagPopover"
      @show="isPopoverOpen = true"
      @hide="isPopoverOpen = false"
    >
      <div class="tag-list popover-tag-list d-flex flex-wrap align-items-center">
        <TagBadge v-for="(tag, index) in tags" :key="tagKey(tag, index)" :tag="tag" />
      </div>
    </Popover>
  </div>
</template>

<script>
import Popover from "primevue/popover";

import BaseIconCounter from "@/components/BaseIconCounter.vue";
import TagBadge from "@/components/TagBadge.vue";

export default {
  components: {
    BaseIconCounter,
    Popover,
    TagBadge,
  },
  props: {
    // Each tag is a reference object `{ type: "tags", immutable_id, name, color }`.
    tags: {
      type: Array,
      default: () => [],
    },
    maxVisible: {
      type: Number,
      default: null,
    },
  },
  data() {
    return {
      isPopoverOpen: false,
    };
  },
  computed: {
    visibleTags() {
      return this.maxVisible === null ? this.tags : this.tags.slice(0, this.maxVisible);
    },
    hiddenTagCount() {
      return Math.max(this.tags.length - this.visibleTags.length, 0);
    },
    hiddenTagsHoverText() {
      return `${this.hiddenTagCount} more tag${this.hiddenTagCount === 1 ? "" : "s"}`;
    },
    counterHoverText() {
      return this.isPopoverOpen ? "" : this.hiddenTagsHoverText;
    },
  },
  watch: {
    hiddenTagCount(count) {
      if (!count) {
        this.isPopoverOpen = false;
      }
    },
  },
  methods: {
    tagKey(tag, index) {
      return tag.immutable_id || `tag-${index}`;
    },
    togglePopover(event) {
      this.$refs.tagPopover.toggle(event);
    },
  },
};
</script>

<style scoped>
/* Layout uses Bootstrap d-flex utilities; only the gap stays as CSS since
   Bootstrap 4 has no gap utilities. */
.tag-list {
  gap: 0.3rem;
}

.more-tags-trigger {
  cursor: pointer;
}

.popover-tag-list {
  max-width: 30rem;
}
</style>
