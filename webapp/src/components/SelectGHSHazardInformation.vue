<template>
  <vSelect
    v-model="selectedGhsCodes"
    :options="ghsOptions"
    multiple
    placeholder="Select GHS codes"
    taggable
    :filterable="false"
    :close-on-select="false"
  >
    <template #option="{ label }">
      <div v-if="label" class="ghs-option" :class="{ selected: selectedGhsCodes.includes(label) }">
        <img :alt="getLabel(label)" :src="getPictogram(label)" class="ghs-icon" />
        <span>{{ label + ": " + getLabel(label) }}</span>
      </div>
    </template>

    <template #selected-option="{ label }">
      <div v-if="label" class="chip-content" @click="handleSelectedOptionClick(label)">
        <img :alt="getLabel(label)" :src="getPictogram(label)" class="ghs-icon" />
      </div>
    </template>
  </vSelect>
</template>

<script>
import { HazardPictograms } from "@/resources.js";
import vSelect from "vue-select";

export default {
  components: {
    vSelect,
  },
  props: {
    modelValue: { type: String, required: true },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      selectedGhsCodes: this.modelValue ? this.modelValue.split(",") : [],
      ghsOptions: Object.keys(HazardPictograms).map((key) => key),
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
      const option = HazardPictograms[value];
      return option ? option.pictogram : "";
    },
    getLabel(value) {
      const option = HazardPictograms[value];
      return option ? option.label : "";
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

.selected {
  color: lightgray;
}

:deep .vs__selected {
  background: none;
}
</style>
