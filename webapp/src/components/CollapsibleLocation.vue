<template>
  <div
    v-if="location"
    class="collapsible-location"
    :class="{ expanded: isExpanded || alwaysExpanded }"
    :title="isExpanded || alwaysExpanded ? '' : location"
    @click="toggle"
  >
    <span v-if="segments.length > 1" class="depth-indicator">
      <span v-for="n in segments.length - 1" :key="n" class="depth-chevron"></span>
    </span>
    <span class="segments-container">
      <span
        v-for="(segment, index) in segments"
        :key="index"
        class="segment-wrapper"
        :class="{ 'parent-segment': index < segments.length - 1 }"
      >
        <span class="segment" :class="{ 'final-segment': index === segments.length - 1 }">
          {{ segment }}
        </span>
        <span v-if="index < segments.length - 1" class="separator"></span>
      </span>
    </span>
  </div>
  <span v-else class="no-location">—</span>
</template>

<script>
export default {
  name: "CollapsibleLocation",
  props: {
    location: {
      type: String,
      default: "",
    },
    alwaysExpanded: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isExpanded: false,
    };
  },
  computed: {
    segments() {
      if (!this.location) return [];
      return this.location.split(">").map((s) => s.trim());
    },
    finalSegment() {
      return this.segments.length > 0 ? this.segments[this.segments.length - 1] : "";
    },
  },
  methods: {
    toggle() {
      if (!this.alwaysExpanded) {
        this.isExpanded = !this.isExpanded;
      }
    },
  },
};
</script>

<style scoped>
.collapsible-location {
  display: inline-flex;
  align-items: stretch;
  cursor: pointer;
  font-size: 0.875rem;
  line-height: 1.4;
  border-radius: 4px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  border: 1px solid #c9cdd1;
  user-select: none;
}

.depth-indicator {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
  padding: 0.25rem 0.4rem;
  overflow: hidden;
  max-width: 10rem;
  border-right: 1px solid #c9cdd1;
  transition:
    max-width 0.2s ease-out,
    padding 0.2s ease-out,
    opacity 0.15s ease-out,
    border-width 0.2s ease-out;
}

.collapsible-location.expanded .depth-indicator {
  max-width: 0;
  padding: 0.25rem 0;
  opacity: 0;
  border-right-width: 0;
}

.depth-chevron {
  display: inline-block;
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 5px solid #868e96;
  margin: 0 2px;
}

.segments-container {
  display: inline-flex;
  align-items: stretch;
}

.segment-wrapper {
  display: inline-flex;
  align-items: stretch;
  overflow: hidden;
  transition:
    max-width 0.2s ease-out,
    opacity 0.15s ease-out;
}

.segment-wrapper.parent-segment {
  max-width: 0;
  opacity: 0;
}

.collapsible-location.expanded .segment-wrapper.parent-segment {
  max-width: 20rem;
  opacity: 1;
}

.segment {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
  padding: 0.25rem 0.5rem;
  color: #495057;
  white-space: nowrap;
}

.segment.final-segment {
  font-weight: 500;
  color: #212529;
}

.separator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0;
  height: 0;
  border-top: 0.75rem solid transparent;
  border-bottom: 0.75rem solid transparent;
  border-left: 0.5rem solid #c9cdd1;
  margin-left: -1px;
}

.no-location {
  color: #adb5bd;
}
</style>
