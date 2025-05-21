import { reactive } from "vue";

const state = reactive({
  dialogQueue: [],
  currentDialog: null,
  isProcessing: false,
});

export const DialogService = {
  /**
   * Show an alert dialog
   * @param {Object} options - Dialog options
   * @param {string} options.title - Dialog title
   * @param {string} options.message - Dialog message
   * @param {string} options.type - Dialog type (info, success, warning, error)
   * @param {string} options.confirmButtonText - Text for the confirm button
   * @returns {Promise} Resolves when dialog is closed
   */
  alert(options) {
    return this.showDialog({
      ...options,
      type: options.type || "info",
      showCancelButton: false,
      confirmButtonText: options.confirmButtonText || "OK",
    });
  },

  /**
   * Show a confirmation dialog
   * @param {Object} options - Dialog options
   * @param {string} options.title - Dialog title
   * @param {string} options.message - Dialog message
   * @param {string} options.type - Dialog type (default: 'confirm')
   * @param {string} options.confirmButtonText - Text for the confirm button
   * @param {string} options.cancelButtonText - Text for the cancel button
   * @returns {Promise<boolean>} Resolves with true if confirmed, false if canceled
   */
  confirm(options) {
    return this.showDialog({
      ...options,
      type: options.type || "confirm",
      showCancelButton: true,
      confirmButtonText: options.confirmButtonText || "Confirm",
      cancelButtonText: options.cancelButtonText || "Cancel",
    });
  },

  /**
   * Show an error dialog
   * @param {string|Object} messageOrOptions - Error message or options object
   * @returns {Promise} Resolves when dialog is closed
   */
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

  /**
   * Show a dialog with the provided options
   * @param {Object} options - Dialog options
   * @returns {Promise} Resolves when dialog is confirmed or canceled
   */
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

  /**
   * Process the dialog queue
   */
  processQueue() {
    if (state.isProcessing || state.dialogQueue.length === 0) {
      return;
    }

    state.isProcessing = true;
    state.currentDialog = state.dialogQueue.shift();
  },

  /**
   * Close the current dialog
   * @param {boolean} confirmed - Whether the dialog was confirmed
   */
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

    // Process the next dialog in the queue
    this.processQueue();
  },

  /**
   * Get the current dialog state
   * @returns {Object} The current dialog state
   */
  getState() {
    return state;
  },
};
