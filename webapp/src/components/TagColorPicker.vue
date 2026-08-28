<template>
  <div class="tag-color-picker d-flex flex-column">
    <div class="swatches d-flex flex-wrap" role="group" aria-label="Tag color presets">
      <button
        v-for="color in palette"
        :key="color"
        type="button"
        class="swatch"
        :class="{ selected: isSelected(color) }"
        :style="{ backgroundColor: color }"
        :title="color"
        :aria-label="`Use color ${color}`"
        :aria-pressed="isSelected(color)"
        @click="select(color)"
      ></button>
    </div>

    <div class="custom-row d-flex align-items-center">
      <label class="custom-label mb-0 d-inline-flex align-items-center">
        Custom:
        <input
          type="color"
          class="color-input"
          :value="modelValue || '#cccccc'"
          aria-label="Custom tag color"
          @input="select($event.target.value)"
        />
      </label>
      <TagBadge :tag="{ name: previewLabel, color: modelValue }" />
    </div>
  </div>
</template>

<script>
import { TAG_COLOR_PALETTE } from "@/resources.js";
import TagBadge from "@/components/TagBadge.vue";

export default {
  name: "TagColorPicker",
  components: {
    TagBadge,
  },
  props: {
    // The selected color as a CSS hex string, or null for no color.
    modelValue: {
      type: String,
      default: null,
    },
    previewLabel: {
      type: String,
      default: "preview",
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      palette: TAG_COLOR_PALETTE,
    };
  },
  methods: {
    isSelected(color) {
      return Boolean(this.modelValue) && this.modelValue.toLowerCase() === color.toLowerCase();
    },
    select(color) {
      this.$emit("update:modelValue", color);
    },
  },
};
</script>

<style scoped>
/* Layout uses Bootstrap d-flex utilities; only the gaps stay as CSS since
   Bootstrap 4 has no gap utilities. */
.tag-color-picker {
  gap: 0.5rem;
}
.swatches {
  gap: 0.35rem;
}
.swatch {
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.25);
  padding: 0;
  cursor: pointer;
}
.swatch.selected {
  outline: 2px solid #0b6093;
  outline-offset: 1px;
}
.custom-row {
  gap: 0.75rem;
}
.custom-label {
  gap: 0.35rem;
}
.color-input {
  width: 2.2rem;
  height: 1.6rem;
  padding: 0;
  border: 1px solid rgba(0, 0, 0, 0.25);
  background: none;
  cursor: pointer;
}
</style>
