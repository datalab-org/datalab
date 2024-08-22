<template>
  <div>
    <QRCodeVue3 :value="appUrl + '/items/' + refcode" :width="width" />
    <button v-show="showPrintButton">Print</button>
  </div>
</template>

<script>
import QRCodeVue3 from "qrcode-vue3";
export default {
  name: "QRCode",
  components: { QRCodeVue3 },
  props: {
    refcode: {
      type: String,
      required: true,
    },
    showPrintButton: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
};
</script>
