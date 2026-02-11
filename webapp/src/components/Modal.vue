<template>
  <div id="dummyDivForModalBackground" :class="{ overlay: modalOpaque }"></div>

  <div
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
          <slot name="footer">
            <input type="submit" class="btn btn-info" :disabled="disableSubmit" value="Submit" />
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
  },
  emits: ["update:modelValue"],
  data() {
    return {
      modalDisplayed: false,
      modalOpaque: false,
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
  methods: {
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
