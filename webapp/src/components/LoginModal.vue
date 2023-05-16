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
        <div class="modal-body ml-auto mr-auto p-8">
          <div>
            <button
              type="button"
              class="login btn-link btn btn-default"
              data-dismiss="modal"
              aria-label="Login with GitHub"
              @click="this.apiUrl + '/login/github'"
            >
              <span aria-hidden="true">
                <font-awesome-icon :icon="['fab', 'github']" /> Login with GitHub</span
              >
            </button>
          </div>
          <div>
            <button
              type="button"
              class="login btn-link btn btn-default orcid-hover"
              data-dismiss="modal"
              aria-label="Login with ORCID"
              @click="this.apiUrl + '/login/orcid'"
            >
              <span aria-hidden="true">
                <font-awesome-icon :icon="['fab', 'orcid']" /> Login with ORCID</span
              >
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_URL } from "@/resources.js";
export default {
  data() {
    return {
      modalDisplayed: false,
      modalOpaque: false,
      apiUrl: API_URL,
    };
  },
  props: {
    modelValue: Boolean,
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

/* css selector for a font-awesome-icon svg inside a class called orcid-hover that only changes color of the icon */

.orcid-hover:hover > {
  color: #a6ce39;
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
</style>
