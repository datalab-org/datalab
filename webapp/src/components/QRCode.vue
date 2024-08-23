<template>
  <div>
    <QRCodeVue3
      :value="qrCodeResolverURL + '/' + refcode"
      :width="width"
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
  </div>
</template>

<script>
import QRCodeVue3 from "qrcode-vue3";
import QR_CODE_RESOLVER_URL from "@/resources.js";

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
      qrCodeResolverURL: QR_CODE_RESOLVER_URL,
    };
  },
};
</script>
