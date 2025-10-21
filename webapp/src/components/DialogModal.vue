<template>
  <Teleport to="body">
    <div v-if="isVisible" class="modal fade show d-block" @click.self="handleOverlayClick">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ title }}</h5>
            <button v-if="showCloseButton" type="button" class="close" @click="cancel">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <div class="d-flex align-items-start">
              <div v-if="type === 'error'" class="mr-3 text-danger">
                <font-awesome-icon icon="exclamation-circle" size="2x" />
              </div>
              <div v-else-if="type === 'warning'" class="mr-3 text-warning flex-shrink-0">
                <font-awesome-icon icon="exclamation-triangle" size="2x" />
              </div>
              <div v-else-if="type === 'info'" class="mr-3 text-info flex-shrink-0">
                <font-awesome-icon icon="info-circle" size="2x" />
              </div>
              <div v-else-if="type === 'success'" class="mr-3 text-success flex-shrink-0">
                <font-awesome-icon icon="check-circle" size="2x" />
              </div>

              <div class="flex-grow-1 text-break">
                <!-- eslint-disable-next-line vue/no-v-html -->
                <p v-if="message" class="mb-0 text-break" v-html="message"></p>
                <slot></slot>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button
              v-if="showCancelButton"
              data-testid="dialog-modal-cancel-button"
              type="button"
              class="btn btn-secondary"
              @click="cancel"
            >
              {{ cancelButtonText }}
            </button>
            <button
              type="button"
              data-testid="dialog-modal-confirm-button"
              class="btn"
              :class="confirmButtonClass"
              @click="confirm"
            >
              {{ confirmButtonText }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="isVisible" class="modal-backdrop fade show"></div>
  </Teleport>
</template>

<script>
export default {
  name: "DialogModal",
  props: {
    title: {
      type: String,
      default: "Dialog",
    },
    message: {
      type: String,
      default: "",
    },
    type: {
      type: String,
      default: "info",
      validator: (value) => ["info", "warning", "error", "success", "confirm"].includes(value),
    },
    confirmButtonText: {
      type: String,
      default: "OK",
    },
    cancelButtonText: {
      type: String,
      default: "Cancel",
    },
    showCancelButton: {
      type: Boolean,
      default: false,
    },
    showCloseButton: {
      type: Boolean,
      default: true,
    },
    closeOnOverlayClick: {
      type: Boolean,
      default: false,
    },
    isVisible: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["confirm", "cancel", "update:isVisible"],
  computed: {
    confirmButtonClass() {
      const classes = {
        info: "btn-info",
        warning: "btn-warning",
        error: "btn-danger",
        success: "btn-success",
        confirm: "btn-primary",
      };
      return classes[this.type] || "btn-primary";
    },
  },
  methods: {
    confirm() {
      this.$emit("confirm");
      this.$emit("update:isVisible", false);
    },
    cancel() {
      this.$emit("cancel");
      this.$emit("update:isVisible", false);
    },
    handleOverlayClick() {
      if (this.closeOnOverlayClick) {
        this.cancel();
      }
    },
  },
};
</script>
