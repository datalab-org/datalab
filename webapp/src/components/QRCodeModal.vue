<template>
  <form class="modal-enclosure" data-testid="qrcode-form">
    <Modal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
      <template #header>QR Code</template>
      <template #body>
        <div class="form-row">
          <div ref="qrcode" class="form-group mx-auto" data-testid="qrcode">
            <QRCode :refcode="refcode" />
          </div>
        </div>
      </template>
      <template #footer>
        <button type="submit" class="btn btn-info" value="Print" @click="printQR">Print</button>
        <button
          type="button"
          class="btn btn-secondary"
          data-dismiss="modal"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </button>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import QRCode from "@/components/QRCode.vue";
export default {
  name: "QRCodeModal",
  components: {
    QRCode,
    Modal,
  },
  props: {
    modelValue: Boolean,
    refcode: { type: String, required: true },
  },
  emits: ["update:modelValue"],
  methods: {
    printQR() {
      const printContents = this.$refs.qrcode.innerHTML;
      const printWindow = window.open("", "", "height=400, width=800");

      printWindow.document.write(
        "<html><head><title>QR Code</title></head><body>" + printContents + "</body></html>",
      );
      printWindow.document.close();
      printWindow.print();
    },
  },
};
</script>
