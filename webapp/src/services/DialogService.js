import { reactive } from "vue";

const state = reactive({
  dialogQueue: [],
  currentDialog: null,
  isProcessing: false,
});

export const DialogService = {
  alert(options) {
    return this.showDialog({
      ...options,
      type: options.type || "info",
      showCancelButton: false,
      confirmButtonText: options.confirmButtonText || "OK",
    });
  },

  confirm(options) {
    return this.showDialog({
      ...options,
      type: options.type || "confirm",
      showCancelButton: true,
      confirmButtonText: options.confirmButtonText || "Confirm",
      cancelButtonText: options.cancelButtonText || "Cancel",
    });
  },

  error(messageOrOptions) {
    const options =
      typeof messageOrOptions === "string" ? { message: messageOrOptions } : messageOrOptions;

    return this.alert({
      title: options.title || "Error",
      message: options.message,
      type: "error",
      confirmButtonText: options.confirmButtonText || "OK",
    });
  },

  showDialog(options) {
    return new Promise((resolve) => {
      const dialogConfig = {
        ...options,
        onConfirm: () => resolve(true),
        onCancel: () => resolve(false),
      };

      state.dialogQueue.push(dialogConfig);
      this.processQueue();
    });
  },

  processQueue() {
    if (state.isProcessing || state.dialogQueue.length === 0) {
      return;
    }

    state.isProcessing = true;
    state.currentDialog = state.dialogQueue.shift();
  },

  closeCurrentDialog(confirmed) {
    if (!state.currentDialog) {
      return;
    }

    if (confirmed) {
      state.currentDialog.onConfirm && state.currentDialog.onConfirm();
    } else {
      state.currentDialog.onCancel && state.currentDialog.onCancel();
    }

    state.currentDialog = null;
    state.isProcessing = false;

    this.processQueue();
  },

  getState() {
    return state;
  },
};
