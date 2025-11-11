<template>
  <DialogModal
    v-if="currentDialog"
    v-model:isVisible="isVisible"
    :title="currentDialog.title"
    :message="currentDialog.message"
    :type="currentDialog.type"
    :confirm-button-text="currentDialog.confirmButtonText"
    :cancel-button-text="currentDialog.cancelButtonText"
    :show-cancel-button="currentDialog.showCancelButton"
    :show-close-button="currentDialog.showCloseButton"
    :close-on-overlay-click="currentDialog.closeOnOverlayClick"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  />
</template>

<script>
import { DialogService } from "@/services/DialogService";
import DialogModal from "./DialogModal.vue";

export default {
  name: "DialogContainer",
  components: {
    DialogModal,
  },
  data() {
    return {
      isVisible: false,
    };
  },
  computed: {
    currentDialog() {
      return DialogService.getState().currentDialog;
    },
  },
  watch: {
    currentDialog(newValue) {
      this.isVisible = !!newValue;
    },
  },
  methods: {
    handleConfirm() {
      DialogService.closeCurrentDialog(true);
    },
    handleCancel() {
      DialogService.closeCurrentDialog(false);
    },
  },
};
</script>
