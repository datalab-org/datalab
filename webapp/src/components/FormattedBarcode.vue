<template>
  <span v-if="barcode">
    <font-awesome-icon
      v-if="enableBarcode"
      icon="barcode"
      class="badge clickable"
      title="Click to show Barcode for this item"
      aria-label="Click to show Barcode for this item"
      @click="BarcodeModalOpen = true"
    />
    <font-awesome-icon v-else icon="barcode" class="badge" />
    <span
      class="badge clickable"
      data-testid="formatted-barcode"
      :style="{ backgroundColor: badgeColor }"
    >
      {{ barcode }}
    </span>
    <div v-if="enableBarcode">
      <BarcodeModal v-model="BarcodeModalOpen" :barcode="barcode" />
    </div>
  </span>
</template>

<script>
import BarcodeModal from "@/components/BarcodeModal.vue";

export default {
  components: {
    BarcodeModal,
  },
  props: {
    barcode: {
      // Items without a barcode store an explicit `null`, which bypasses prop
      // defaults, so this cannot be `required`. The template guards on it.
      type: String,
      default: null,
    },
    enableBarcode: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      BarcodeModalOpen: false,
    };
  },
  computed: {
    badgeColor() {
      return "LightGrey";
    },
  },
};
</script>

<style scoped>
.badge {
  color: black;
  text-align: center;
  vertical-align: middle;
}
</style>
