<template>
  <div
    ref="modalRef"
    class="modal fade"
    tabindex="-1"
    role="dialog"
    :class="{ show: modalOpaque }"
    :style="{ display: modalDisplayed ? 'block' : 'none' }"
    aria-modal="true"
  >
    <div class="modal-dialog" :class="{ 'modal-lg': isLarge }" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <slot name="header"></slot>
          </h5>
          <button type="button" class="btn-close" aria-label="Close" @click="closeModal"></button>
        </div>
        <div class="modal-body">
          <slot name="body"></slot>
        </div>
        <div class="modal-footer">
          <slot name="footer">
            <input
              type="submit"
              class="btn btn-info custom-btn-info"
              :disabled="disableSubmit"
              value="Submit"
            />
            <button type="button" class="btn btn-secondary" @click="closeModal">Close</button>
          </slot>
        </div>
      </div>
    </div>
  </div>

  <div v-if="modalDisplayed" class="modal-backdrop fade" :class="{ show: modalOpaque }"></div>
</template>

<script>
export default {
  props: {
    modelValue: Boolean,
    disableSubmit: {
      type: Boolean,
      default: false,
    },
    isLarge: {
      type: Boolean,
      default: false,
    },
    transitionDuration: {
      type: Number,
      default: 300,
    },
  },
  emits: ["update:modelValue", "opened", "closed"],
  data() {
    return {
      modalDisplayed: false,
      modalOpaque: false,
    };
  },
  watch: {
    modelValue(newValue) {
      if (newValue && !this.modalDisplayed) {
        this.openModal();
      } else if (!newValue && this.modalDisplayed) {
        this.closeModal();
      }
    },
  },
  mounted() {
    if (this.modelValue) {
      this.openModal();
    }

    document.addEventListener("keydown", this.handleEscKey);
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this.handleEscKey);

    if (this.modalDisplayed) {
      document.body.classList.remove("modal-open");
    }
  },
  methods: {
    async openModal() {
      document.body.classList.add("modal-open");

      this.modalDisplayed = true;

      requestAnimationFrame(() => {
        this.modalOpaque = true;

        this.$nextTick(() => {
          this.trapFocus();
          this.$emit("opened");
        });
      });
    },
    async closeModal() {
      this.modalOpaque = false;

      await new Promise((resolve) => {
        const duration = this.transitionDuration;
        setTimeout(resolve, duration);
      });

      this.modalDisplayed = false;

      document.body.classList.remove("modal-open");

      this.$emit("update:modelValue", false);
      this.$emit("closed");
    },
    handleEscKey(event) {
      if (event.key === "Escape" && this.modalDisplayed) {
        this.closeModal();
      }
    },
    trapFocus() {
      const modalElement = this.$refs.modalRef;

      if (!modalElement) return;

      const focusableElements = modalElement.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );

      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    },
  },
};
</script>

<style scoped>
.modal {
  z-index: 1050;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1040;
}

.fade {
  opacity: 0;
  transition: opacity 0.3s linear;
}

.fade.show {
  opacity: 1;
}

.btn:disabled {
  cursor: not-allowed;
}

/* Bootstrap 4 color's */
.custom-btn-info {
  color: #fff;
  background-color: #17a2b8;
  border-color: #17a2b8;
}
</style>
