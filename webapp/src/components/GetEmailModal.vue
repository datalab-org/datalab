<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(successMessage) || !Boolean(emailAddress)"
    >
      <template v-slot:body>
        <div class="form-row">
          <div class="form-group">
            <label for="sample-id" class="col-form-label"
              >Enter your email address to receive a sign-in/registration link:</label
            >
            <input
              v-model="emailAddress"
              type="text"
              class="form-control"
              id="email-address"
              required
            />
            <div class="form-error">{{ emailValidationMessage }}</div>
            <div class="form-success">{{ successMessage }}</div>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { requestMagicLink } from "@/server_fetch_utils.js";
export default {
  name: "CreateSampleModal",
  data() {
    return {
      emailAddress: null,
      emailSent: false,
      emailError: null,
      emailValidationMessage: "",
      successMessage: "",
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  methods: {
    async submitForm() {
      this.validateEmail();
      if (this.emailValidationMessage) {
        return;
      }
      let response = await requestMagicLink(this.emailAddress);
      if (response.status == "success") {
        this.emailSent = true;
        this.successMessage =
          "Email sent! Please check your inbox (and spam folder) for a link to sign in or register. It may take a few minutes to arrive.";
      } else {
        this.emailError = true;
        this.emailValidationMessage =
          "Email failed to send; please verify the address you entered and try again.";
      }
    },
    validateEmail() {
      if (this.emailAddress == null) {
        this.emailValidationMessage = "Please enter your email address.";
      } else if (!/^\S+@\S+\.\S+$/.test(this.emailAddress)) {
        this.emailValidationMessage =
          "Email address appears to be invalid; please verify and contact us if this error persists.";
      } else {
        this.emailValidationMessage = "";
      }
    },
  },
  components: {
    Modal,
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

.form-success {
  color: dodgerblue;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}
.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}
</style>
