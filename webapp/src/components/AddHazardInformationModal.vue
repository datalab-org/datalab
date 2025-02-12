<template>
  <form class="modal-enclosure" data-testid="add-h-codes-form" @submit.prevent="submitForm">
    <Modal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
      <template #header> Add Hazard information </template>
      <template #body>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="items-selected" class="col-form-label">Item:</label>
            <div id="items-selected" class="dynamic-input">
              <FormattedItemName :item_id="item_id" :item-type="type" enable-click />
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="addToCollectionLabel">Hazard information:</label>
            <input
              id="h-codes-input"
              v-model="hazardInformation"
              type="text"
              class="form-control"
              placeholder="Enter hazard information (H codes included)"
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import FormattedItemName from "@/components/FormattedItemName";

export default {
  name: "AddHazardInformationModal",
  components: {
    Modal,
    FormattedItemName,
  },
  props: {
    modelValue: Boolean,
    ghs: { type: String, default: "" },
    item_id: { type: String, required: true },
    type: { type: String, required: true },
  },
  emits: ["update:modelValue", "submitHazardInformation"],
  data() {
    return {
      hazardInformation: this.ghs || "",
    };
  },
  watch: {
    ghs(newVal) {
      this.hazardInformation = newVal;
    },
  },
  methods: {
    async submitForm() {
      this.$emit("submitHazardInformation", this.hazardInformation);
      this.$emit("update:modelValue", false);
    },
  },
};
</script>

<style scoped></style>
