<template>
  <div class="ghs-display form-control">
    <div v-for="pictogram in selectedPictograms" :key="pictogram.label" class="ghs-chip">
      <img :alt="pictogram.label" :src="pictogram.pictogram" class="ghs-icon" />
      <span>{{ pictogram.label }}</span>
    </div>
    <font-awesome-icon
      class="plus-icon"
      :icon="['fa', 'plus']"
      @click="AddHazardInformationModalIsOpen = true"
    />
  </div>
  <AddHazardInformationModal
    v-model="AddHazardInformationModalIsOpen"
    :ghs="modelValue"
    :item_id="item_id"
    :type="type"
    @submit-hazard-information="updateGHS"
  />
</template>

<script>
import { getPictogramsFromHazardInformation } from "@/resources.js";
import AddHazardInformationModal from "@/components/AddHazardInformationModal.vue";

export default {
  components: {
    AddHazardInformationModal,
  },
  props: {
    modelValue: { type: String, required: true },
    item_id: { type: String, required: true },
    type: { type: String, required: true },
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
.ghs-display {
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: calc(1.5em + 0.75rem + 2px);
  height: auto;
  gap: 0.3rem;
}

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
  width: 1.6rem;
  height: 1.6rem;
  margin-right: 8px;
}

.plus-icon {
  position: absolute;
  color: black;
  top: 0.6rem;
  right: 0.6rem;
}
</style>
