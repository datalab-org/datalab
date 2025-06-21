<template>
  <span v-if="enableQRCode" class="badge clickable" @click="QRCodeModalOpen = true">
    <font-awesome-icon
      icon="qrcode"
      title="Click to show QR Code for this item"
      aria-label="Click to show QR Code for this item"
    />
  </span>
  <span
    class="badge"
    :class="{ clickable: enableClick || enableModifiedClick }"
    :style="{ backgroundColor: badgeColor }"
    @click.exact="enableClick ? openEditPageInNewTab() : null"
    @click.meta.stop="enableModifiedClick ? openEditPageInNewTab() : null"
    @click.ctrl.stop="enableModifiedClick ? openEditPageInNewTab() : null"
  >
    {{ refcode }}
  </span>
  <div v-if="enableQRCode">
    <QRCodeModal v-model="QRCodeModalOpen" :refcode="refcode" />
  </div>
</template>

<script>
import QRCodeModal from "@/components/QRCodeModal.vue";

export default {
  components: {
    QRCodeModal,
  },
  props: {
    refcode: {
      type: String,
      required: true,
    },
    enableClick: {
      type: Boolean,
      default: false,
    },
    enableQRCode: {
      type: Boolean,
      default: true,
    },
    enableModifiedClick: {
      type: Boolean,
      default: false,
    },
    maxLength: {
      type: Number,
      default: NaN,
    },
  },
  emits: ["itemIdClicked"],
  data() {
    return {
      QRCodeModalOpen: false,
    };
  },
  computed: {
    badgeColor() {
      return "LightGrey";
    },
  },
  methods: {
    openEditPageInNewTab() {
      this.$emit("itemIdClicked");
      window.open(`/items/${this.refcode}`, "_blank");
    },
  },
};
</script>

<style scoped>
.badge {
  color: black;
}
</style>
