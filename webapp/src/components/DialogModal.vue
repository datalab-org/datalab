<template>
  <Teleport to="body">
    <div v-if="isVisible" class="dialog-overlay" @click.self="handleOverlayClick">
      <div class="dialog-modal">
        <div class="dialog-header">
          <h5 class="dialog-title">{{ title }}</h5>
          <button v-if="showCloseButton" type="button" class="close" @click="cancel">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="dialog-body">
          <div v-if="type === 'error'" class="dialog-icon error-icon">
            <font-awesome-icon icon="exclamation-circle" size="2x" />
          </div>
          <div v-else-if="type === 'warning'" class="dialog-icon warning-icon">
            <font-awesome-icon icon="exclamation-triangle" size="2x" />
          </div>
          <div v-else-if="type === 'info'" class="dialog-icon info-icon">
            <font-awesome-icon icon="info-circle" size="2x" />
          </div>
          <div v-else-if="type === 'success'" class="dialog-icon success-icon">
            <font-awesome-icon icon="check-circle" size="2x" />
          </div>

          <div class="dialog-content">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <p v-if="message" v-html="message"></p>
            <slot></slot>
          </div>
        </div>
        <div class="dialog-footer">
          <button v-if="showCancelButton" type="button" class="btn btn-secondary" @click="cancel">
            {{ cancelButtonText }}
          </button>
          <button type="button" class="btn" :class="confirmButtonClass" @click="confirm">
            {{ confirmButtonText }}
          </button>
        </div>
      </div>
    </div>
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

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.dialog-modal {
  background-color: white;
  border-radius: 0.3rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: dialog-fade-in 0.3s;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.dialog-title {
  margin: 0;
  line-height: 1.5;
}

.dialog-body {
  padding: 1rem;
  display: flex;
  align-items: flex-start;
}

.dialog-icon {
  margin-right: 1rem;
  min-width: 2em;
}

.dialog-content {
  flex-grow: 1;
}

.error-icon {
  color: #dc3545;
}

.warning-icon {
  color: #ffc107;
}

.info-icon {
  color: #17a2b8;
}

.success-icon {
  color: #28a745;
}

.dialog-footer {
  padding: 1rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

@keyframes dialog-fade-in {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
