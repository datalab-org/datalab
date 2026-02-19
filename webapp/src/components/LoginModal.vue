<template>
  <DialogModal
    :is-visible="loginState.isVisible"
    title="Login Required"
    :message="loginState.message"
    type="info"
    confirm-button-text="Cancel"
    :show-close-button="true"
    @confirm="hide"
    @cancel="hide"
  >
    <LoginDropdown />
  </DialogModal>
</template>

<script>
import { LoginService } from "@/services/LoginService";
import DialogModal from "./DialogModal.vue";
import LoginDropdown from "./LoginDropdown.vue";

export default {
  name: "LoginModal",
  components: {
    DialogModal,
    LoginDropdown,
  },
  computed: {
    loginState() {
      return LoginService.getState();
    },
  },
  methods: {
    hide() {
      LoginService.hide();
    },
  },
};
</script>
