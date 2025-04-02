<template>
  <div class="ghs-display ml-2 mt-2">
    <span v-for="pictogram in selectedPictograms" :key="pictogram.label">
      <img
        :title="pictogram.label"
        :alt="pictogram.label"
        :src="pictogram.pictogram"
        class="ghs-icon"
      />
    </span>
  </div>
</template>

<script>
import { getPictogramsFromHazardInformation } from "@/resources.js";

export default {
  props: {
    modelValue: { type: String, required: true },
  },
  emits: ["update:modelValue"],

  data() {
    return {
      AddHazardInformationModalIsOpen: false,
      selectedPictograms: [],
    };
  },
  watch: {
    modelValue(newVal) {
      this.updateSelectedPictograms(newVal);
    },
  },
  mounted() {
    this.updateSelectedPictograms(this.modelValue);
  },
  methods: {
    updateSelectedPictograms() {
      if (!this.modelValue) {
        this.selectedPictograms = [];
        return;
      }

      this.selectedPictograms = getPictogramsFromHazardInformation(this.modelValue);
    },
    updateGHS(newGHS) {
      this.$emit("update:modelValue", newGHS);
      this.updateSelectedPictograms(newGHS);
    },
  },
};
</script>

<style scoped>
.ghs-content {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.ghs-chip {
  display: flex;
  align-items: center;
}

.ghs-icon {
  width: 8rem;
  height: 8rem;
  margin-right: 8px;
}
</style>
