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
    <div
      ref="contentContainer"
      class="comparison-content-container"
      :style="{ 'max-height': maxHeight }"
    >
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
      <div class="form-row mt-2 mb-3">
        <button class="btn btn-primary btn-sm" @click="applySelection">
          {{ applyButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import FileMultiSelectDropdown from "@/components/FileMultiSelectDropdown";

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
  },
  emits: ["update:modelValue", "apply"],
  data() {
    return {
      internalFileModel: [],
      maxHeight: "0px",
      paddingHeight: 18,
      isExpanded: false,
    };
  },
  watch: {
    modelValue(newVal) {
      this.internalFileModel = newVal.slice();
    },
  },
  mounted() {
    // Initialize internal model from prop
    this.internalFileModel = this.modelValue.slice();

    // Set initial expanded state
    this.isExpanded = this.initiallyExpanded;

    // Initialize collapse state
    var contentContainer = this.$refs.contentContainer;
    if (contentContainer) {
      if (this.isExpanded) {
        this.maxHeight = "none";
        contentContainer.style.overflow = "visible";
      } else {
        this.maxHeight = "0px";
      }

      contentContainer.addEventListener("transitionend", () => {
        if (this.isExpanded) {
          this.maxHeight = "none";
        }
      });
    }
  },
  methods: {
    toggleExpanded() {
      var content = this.$refs.contentContainer;
      if (!this.isExpanded) {
        this.maxHeight = content.scrollHeight + 2 * this.paddingHeight + "px";
        this.isExpanded = true;
        content.style.overflow = "visible";
      } else {
        content.style.overflow = "hidden";
        requestAnimationFrame(() => {
          this.maxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.maxHeight = "0px";
            this.isExpanded = false;
          });
        });
      }
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

.comparison-content-container {
  overflow: hidden;
  max-height: none;
  transition: max-height 0.4s ease-in-out;
}
</style>
