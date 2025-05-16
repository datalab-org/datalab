<template>
  <form class="modal-enclosure" data-testid="barcode-form">
    <Modal
      :model-value="modelValue"
      :disable-submit="true"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header>Barcode</template>
      <template #body>
        <div class="row justify-content-center">
          <div ref="barcode" class="text-center barcode-display" data-testid="barcode">
            {{ barcode }}
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
export default {
  name: "BarcodeModal",
  components: {
    Modal,
  },
  props: {
    modelValue: Boolean,
    barcode: { type: String, required: true },
  },
  emits: ["update:modelValue"],
};
</script>

<style scoped>
.barcode-display {
  font-family: "Libre Barcode 39 Text";
  font-size: 5rem;
}
</style>
