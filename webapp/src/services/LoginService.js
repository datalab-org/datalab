import { reactive } from "vue";

const state = reactive({
  isVisible: false,
  message: "",
});

export const LoginService = {
  show(message = "You need to log in to access this resource.") {
    state.isVisible = true;
    state.message = message;
  },

  hide() {
    state.isVisible = false;
    state.message = "";
  },

  getState() {
    return state;
  },
};
