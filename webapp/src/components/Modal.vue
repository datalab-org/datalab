<template>
  <div id="dummyDivForModalBackground" :class="{ overlay: modalOpaque }"></div>

  <div
    ref="modal"
    class="modal fade"
    tabindex="-1"
    role="dialog"
    :style="{ display: modalDisplayed ? 'block' : 'none' }"
    :class="{ show: modalOpaque }"
  >
    <div class="modal-dialog" :class="{ 'modal-lg': isLarge }" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <slot name="header"></slot>
          </h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true" @click="closeModal">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <slot name="body"></slot>
        </div>
        <div class="modal-footer">
          <slot name="footer" :submitting="submitting">
            <input
              type="submit"
              class="btn btn-info"
              :disabled="disableSubmit || submitting"
              value="Submit"
            />

            <button
              type="button"
              class="btn btn-secondary"
              data-dismiss="modal"
              @click="closeModal"
            >
              Close
            </button>
          </slot>
        </div>
      </div>
    </div>
  </div>
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
      default: true,
    },
    onSubmit: {
      type: Function,
      default: null,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      modalDisplayed: false,
      modalOpaque: false,
      submitting: false,
      form: null,
    };
  },
  watch: {
    modelValue(newValue) {
      if (newValue) {
        this.openModal();
      }
      if (!newValue) {
        this.closeModal();
      }
    },
  },
  mounted() {
    this.form = this.$refs.modal.closest("form");
    this.form?.addEventListener("submit", this.handleFormSubmit);
  },
  beforeUnmount() {
    this.form?.removeEventListener("submit", this.handleFormSubmit);
  },
  methods: {
    /**
     * Runs the `@submit` handler for the enclosing form (from the submit button or the Enter key),
     * ignoring further submissions until it settles so that slow requests cannot be sent twice.
     * The lock is released whether or not the handler succeeds, so a failed submission can be retried.
     */
    async handleFormSubmit(event) {
      if (!this.onSubmit) {
        return;
      }
      event.preventDefault();
      if (this.submitting) {
        return;
      }
      this.submitting = true;
      try {
        await this.onSubmit(event);
      } finally {
        this.submitting = false;
      }
    },
    async openModal() {
      this.modalDisplayed = true;
      await new Promise((resolve) => setTimeout(resolve, 20)); //hacky...
      this.$nextTick(() => {
        this.modalOpaque = true;
      });
    },
    async closeModal() {
      this.modalOpaque = false;
      await new Promise((resolve) => setTimeout(resolve, 200)); // super hacky
      this.modalDisplayed = false;
      this.$emit("update:modelValue", false);
    },
  },
};
</script>

<style scoped>
.fade {
  opacity: 0;
  transition: opacity 0.15s linear;
}
.fade.show {
  opacity: 1;
}

#dummyDivForModalBackground.overlay:after {
  content: "";
  display: block;
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.2);
}

.btn:disabled {
  cursor: not-allowed;
}

.modal-dialog {
  margin: 5vh auto;
}

.modal-content {
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.modal-body {
  overflow: visible;
  flex: 1;
}
</style>
