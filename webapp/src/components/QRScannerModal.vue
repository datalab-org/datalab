<template>
  <form class="modal-enclosure" data-testid="qrcode-scanner">
    <Modal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
      <template #header>Scan QR Code</template>
      <template #body>
        <div v-if="modelValue" class="form-row">
          <div v-if="decodedQR != null">
            <p>Decoded QR: {{ decodedQR }}</p>
          </div>
          <div v-else>
            <div v-show="!cameraReady">
              <font-awesome-icon
                v-if="!cameraReady"
                icon="spinner"
                class="fa-spin mx-auto"
                fixed-width
                style="color: gray"
                size="2x"
              />
              <div class="alert alert-info text-center">
                No camera available. You may need to allow this page to have camera access in your
                browser.
              </div>
            </div>
            <div
              v-show="cameraReady"
              ref="qrcode-scanner"
              class="form-group mx-auto"
              data-testid="qrcode-scanner"
            >
              <QrcodeStream @camera-on="cameraReady = true" @detect="onDetect" />
            </div>
            <div ref="qrcode-upload" data-testid="qrcode-upload">
              <div>Or upload an image:</div>
              <QrcodeCapture id="upload-qr" class="button button-default" @detect="onDetect" />
            </div>
          </div>
        </div>
      </template>
      <template #footer>
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
import { QrcodeStream, QrcodeCapture } from "vue-qrcode-reader";
export default {
  name: "QRScannerModal",
  components: {
    Modal,
    QrcodeCapture,
    QrcodeStream,
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  data() {
    return {
      decodedQR: null,
      cameraReady: false,
    };
  },
  methods: {
    onDetect(detectedQRs) {
      this.decodedQR = detectedQRs[0].rawValue;
      // Reset camera stream div
      this.cameraReady = false;
    },
  },
};
</script>
