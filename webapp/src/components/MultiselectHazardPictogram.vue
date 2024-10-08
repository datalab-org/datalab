<template>
  <div>
    <MultiSelect
      v-model="selectedGhsCodes"
      :options="ghsOptions"
      class="form-control"
      option-label="label"
      option-value="value"
      placeholder="Select GHS codes"
      display="chip"
      :include-select-all-option="false"
    >
      <template #option="slotProps">
        <div class="ghs-option">
          <img :alt="slotProps.option.label" :src="slotProps.option.pictogram" class="ghs-icon" />
          <div>{{ slotProps.option.value + ": " + slotProps.option.label }}</div>
        </div>
      </template>

      <template #chip="chipProps">
        <div class="chip-content">
          <img :alt="chipProps.value" :src="getPictogram(chipProps.value)" class="ghs-icon" />
        </div>
      </template>
    </MultiSelect>
  </div>
</template>

<script>
import MultiSelect from "primevue/multiselect";
import { HazardPictograms } from "@/resources.js";

export default {
  components: {
    MultiSelect,
  },
  props: {
    modelValue: { type: String, required: true },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      selectedGhsCodes: this.modelValue ? this.modelValue.split(",") : [],
      ghsOptions: Object.entries(HazardPictograms).map(([code, { label, pictogram }]) => ({
        value: code,
        label,
        pictogram,
      })),
    };
  },
  watch: {
    modelValue(newVal) {
      this.selectedGhsCodes = newVal.split(",");
    },
    selectedGhsCodes(newVal) {
      this.$emit("update:modelValue", newVal.join(","));
    },
  },
  methods: {
    getPictogram(value) {
      const option = this.ghsOptions.find((opt) => opt.value === value);
      return option ? option.pictogram : "";
    },
  },
};
</script>

<style scoped>
.ghs-option {
  display: flex;
  align-items: center;
}

.ghs-icon {
  width: 1.6rem;
  height: 1.6rem;
  margin-right: 8px;
}

:deep(.p-multiselect-label) {
  padding: 0 !important;
}
</style>
