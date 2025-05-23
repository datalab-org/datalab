<template>
  <div class="text-center">
    <QRCodeVue3
      :value="QRCodeUrl"
      :width="width"
      :height="width"
      :qr-options="{ typeNumber: 0, mode: 'Byte', errorCorrectionLevel: 'H' }"
      :image-options="{ hideBackgroundDots: false, imageSize: 0, margin: 0 }"
      :dots-options="{
        type: 'square',
        color: 'black',
      }"
      :background-options="{ color: '#ffffff' }"
      :corners-square-options="{ type: 'square', color: 'black' }"
      :corners-dot-options="{ type: 'square', color: 'black' }"
      file-ext="png"
    />
    <div
      id="qrcode-text-label"
      :style="{ width: width }"
      class="qrcode-text-label mx-auto text-center center-text"
    >
      {{ refcode }}
    </div>
  </div>
  <div v-if="!federatedQR" class="alert alert-info">
    QR_CODE_RESOLVER_URL is not set to the federation resolver URL for this deployment.<br />
    Links embedded within QR codes generated here will only work if this <i>datalab</i> instance
    remains at the same URL.<br /><br />

    Visit <a :href="federationQRCodeUrl">{{ federationQRCodeUrl }}</a> to learn about persistent URL
    resolution in <i>datalab</i>.
  </div>
</template>

<script>
import QRCodeVue3 from "qrcode-vue3";
import { FEDERATION_QR_CODE_RESOLVER_URL, QR_CODE_RESOLVER_URL, API_URL } from "@/resources.js";

export default {
  name: "QRCode",
  components: {
    QRCodeVue3,
  },
  props: {
    refcode: {
      type: String,
      required: true,
    },
    width: {
      type: Number,
      default: 200,
    },
  },
  data() {
    return {
      federationQRCodeUrl: FEDERATION_QR_CODE_RESOLVER_URL,
    };
  },
  computed: {
    federatedQR() {
      return FEDERATION_QR_CODE_RESOLVER_URL == QR_CODE_RESOLVER_URL;
    },
    QRCodeUrl() {
      // If the QR_CODE_RESOLVER_URL is not set, use the API_URL
      // with the redirect-to-ui option
      if (QR_CODE_RESOLVER_URL == null) {
        return API_URL + "/items/" + this.refcode + "?redirect-to-ui=true";
      }
      return QR_CODE_RESOLVER_URL + "/" + this.refcode;
    },
  },
};
</script>

<style scoped>
.qrcode-text-label {
  font-family: var(--font-monospace);
  font-size: 1.8rem;
}
</style>
