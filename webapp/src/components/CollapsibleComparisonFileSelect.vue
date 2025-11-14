<template>
  <div>
    <div class="comparison-header collapsible" :class="{ expanded: isExpanded }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        @click="toggleExpanded"
      />
      <span class="comparison-title" @click="toggleExpanded">{{ title }}</span>
    </div>
    <Transition
      name="expand"
      @before-enter="beforeEnter"
      @enter="enter"
      @after-enter="afterEnter"
      @before-leave="beforeLeave"
      @leave="leave"
    >
      <div v-if="isExpanded" ref="contentContainer" class="comparison-content-container">
        <div class="form-row align-items-center mb-2">
          <FileMultiSelectDropdown
            v-model="internalFileModel"
            :item_id="item_id"
            :block_id="block_id"
            :extensions="extensions"
            :update-block-on-change="false"
            :exclude-file-ids="excludeFileIds"
          />
        </div>
        <div v-if="showApplyButton" class="form-row mt-2 mb-3">
          <button class="btn btn-primary btn-sm" @click="applySelection">
            {{ applyButtonText }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
import FileMultiSelectDropdown from "@/components/FileMultiSelectDropdown";

// Padding added to content height for smooth collapse animation
const CONTENT_PADDING_HEIGHT = 18;

export default {
  components: {
    FileMultiSelectDropdown,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    block_id: {
      type: String,
      required: true,
    },
    extensions: {
      type: Array,
      required: true,
    },
    excludeFileIds: {
      type: Array,
      default: () => [],
    },
    modelValue: {
      type: Array,
      default: () => [],
    },
    title: {
      type: String,
      default: "Comparison Files",
    },
    applyButtonText: {
      type: String,
      default: "Apply Comparison Files",
    },
    initiallyExpanded: {
      type: Boolean,
      default: false,
    },
    showApplyButton: {
      type: Boolean,
      default: true,
    },
  },
  emits: ["update:modelValue", "apply"],
  data() {
    return {
      internalFileModel: [],
      isExpanded: false,
    };
  },
  watch: {
    modelValue: {
      handler(newVal) {
        // Avoid triggering the internalFileModel watcher when syncing from parent
        if (JSON.stringify(newVal) !== JSON.stringify(this.internalFileModel)) {
          this.internalFileModel = newVal.slice();
        }
      },
      deep: true,
    },
    internalFileModel: {
      handler(newVal, oldVal) {
        // Emit changes immediately when showApplyButton is false
        // Only emit if the value actually changed
        if (!this.showApplyButton && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
          this.$emit("update:modelValue", newVal.slice());
        }
      },
      deep: true,
    },
  },
  mounted() {
    // Initialize internal model from prop
    this.internalFileModel = this.modelValue.slice();

    // Set initial expanded state
    this.isExpanded = this.initiallyExpanded;
  },
  methods: {
    toggleExpanded() {
      this.isExpanded = !this.isExpanded;
    },

    // Transition hooks for dynamic height animation
    beforeEnter(el) {
      el.style.height = "0";
      el.style.overflow = "hidden";
    },

    enter(el) {
      // Get actual content height including padding
      const height = el.scrollHeight + 2 * CONTENT_PADDING_HEIGHT;
      el.style.height = height + "px";
    },

    afterEnter(el) {
      // Allow content to grow/shrink naturally after animation
      el.style.height = "auto";
      el.style.overflow = "visible";
    },

    beforeLeave(el) {
      // Set current height before collapsing
      el.style.height = el.scrollHeight + "px";
      el.style.overflow = "hidden";
    },

    leave(el) {
      // Force reflow to ensure the height is set before animating
      el.offsetHeight;
      el.style.height = "0";
    },

    applySelection() {
      this.$emit("update:modelValue", this.internalFileModel.slice());
      this.$emit("apply", this.internalFileModel.slice());
    },
  },
};
</script>

<style scoped>
.comparison-header {
  display: flex;
  align-items: center;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.comparison-title {
  margin-left: 0.5em;
  font-size: 1rem;
  font-weight: 500;
  color: #004175;
}

.collapse-arrow {
  color: #004175;
  transition: all 0.4s;
  cursor: pointer;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.expanded .collapse-arrow {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

/* Transition styles for expand/collapse */
.expand-enter-active,
.expand-leave-active {
  transition: height 0.4s ease-in-out;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  height: 0;
}
</style>
