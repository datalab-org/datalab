<template>
  <div class="ghs-display ml-2 mt-2">
    <template v-if="displayPictograms.size > 0">
      <span v-for="pictogram in displayPictograms" :key="pictogram.label">
        <img
          :title="pictogram.label"
          :alt="pictogram.label"
          :src="pictogram.pictogram"
          class="ghs-icon"
        />
      </span>
    </template>
    <template v-else>
      <span class="text-muted">No hazards registered.</span>
    </template>
  </div>
</template>

<script>
import { getPictogramsFromHazardInformation } from "@/resources.js";

export default {
  props: {
    modelValue: { type: String, required: true },
  },
  computed: {
    displayPictograms() {
      if (!this.modelValue) {
        return new Set();
      }
      return getPictogramsFromHazardInformation(this.modelValue);
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
