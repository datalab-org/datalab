<template>
  <template v-if="user != null">
    <div class="dropdown">
      <button
        id="userDropdown"
        class="btn dropdown-toggle border"
        type="button"
        aria-expanded="false"
        data-bs-toggle="dropdown"
      >
        <UserBubbleLogin :creator="user" :size="24" />&nbsp;
        <span class="user-display-name">{{ userDisplayName }}</span
        >&nbsp;
      </button>
      <ul class="dropdown-menu" aria-labelledby="userDropdown">
        <UserDropdown :user="user" />
      </ul>
    </div>
  </template>
  <template v-else-if="!isUserLoaded">
    <div class="dropdown">
      <button
        id="userDropdown"
        class="btn dropdown-toggle border"
        type="button"
        aria-expanded="false"
      >
        <font-awesome-icon icon="spinner" spin />&nbsp;Loading...
      </button>
    </div>
  </template>
  <template v-else>
    <div class="dropdown">
      <button
        id="loginDropdown"
        class="btn border dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        aria-expanded="false"
      >
        <font-awesome-icon icon="sign-in-alt" />&nbsp;Login/Register
      </button>
      <ul class="dropdown-menu" aria-labelledby="loginDropdown">
        <LoginDropdown />
      </ul>
    </div>
  </template>
  <div v-if="isUnverified" class="container mt-4 mb-0 alert alert-warning text-center">
    Your account is currently unverified, and you will be unable to make or edit entries. Please
    contact an administrator.
  </div>
</template>

<script>
import { API_URL } from "@/resources.js";
import UserBubbleLogin from "@/components/UserBubbleLogin.vue";
import { getUserInfo, getInfo } from "@/server_fetch_utils.js";
import UserDropdown from "@/components/UserDropdown.vue";
import LoginDropdown from "@/components/LoginDropdown.vue";

export default {
  components: {
    UserBubbleLogin,
    UserDropdown,
    LoginDropdown,
  },
  props: {
    modelValue: Boolean,
  },
  data() {
    return {
      apiUrl: API_URL,
      user: null,
      isUserLoaded: false,
    };
  },
  computed: {
    userDisplayName() {
      return this.$store.getters.getCurrentUserDisplayName;
    },
    isUnverified() {
      return this.$store.getters.getCurrentUserIsUnverified;
    },
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
  },
  watch: {
    modelValue(newValue) {
      if (newValue) {
        this.openModal();
      } else {
        this.closeModal();
      }
    },
  },
  async mounted() {
    this.getUser();
    if (this.$store.state.serverInfo == null) {
      getInfo();
    }
  },
  methods: {
    async getUser() {
      // Need to reload the page if this is a magic-link login
      let token = this.$route.query.token;
      if (token != null) {
        window.location.href = this.apiUrl + "/login/email?token=" + token;
      }

      this.user = await getUserInfo();
      this.isUserLoaded = true;
      if (this.user != null) {
        this.$store.commit(
          "setIsUnverified",
          this.user.account_status == "unverified" ? true : false,
        );
      }
    },
  },
};
</script>

<style scoped>
.btn:disabled {
  cursor: not-allowed;
}

.user-display-name {
  font-weight: bold;
}
</style>
