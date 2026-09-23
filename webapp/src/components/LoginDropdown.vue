<template>
  <GetEmailModal v-model="emailModalIsOpen" />
  <span v-if="!authMechanismsLoaded" class="dropdown-item text-muted">
    <font-awesome-icon :icon="['fa', 'spinner']" spin /> Loading…
  </span>
  <a
    v-if="showGitHub"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via GitHub"
    :href="loginUrl('github')"
    ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
  >
  <a
    v-if="showORCID"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via ORCID"
    :href="loginUrl('orcid')"
    ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID</a
  >
  <a
    v-if="showGoogle"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via Google"
    :href="loginUrl('google')"
    ><font-awesome-icon :icon="['fab', 'google']" /> Login via Google</a
  >
  <a
    v-if="showMicrosoft"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via Microsoft"
    :href="loginUrl('microsoft')"
    ><font-awesome-icon :icon="['fab', 'microsoft']" /> Login via Microsoft</a
  >
  <button
    v-if="showEmail"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via email"
    @click="emailModalIsOpen = true"
  >
    <font-awesome-icon :icon="['fa', 'envelope']" /> Login via email
  </button>
  <UnsafeTestingPasswordlessLogin v-if="showUnsafeTestingPasswordlessLogin" />
</template>

<script>
import GetEmailModal from "@/components/GetEmailModal.vue";
import UnsafeTestingPasswordlessLogin from "@/components/UnsafeTestingPasswordlessLogin.vue";
import { API_URL } from "@/resources.js";

export default {
  components: {
    GetEmailModal,
    UnsafeTestingPasswordlessLogin,
  },
  props: {
    modelValue: Boolean,
    // Optional app path to return to after an OAuth login
    next: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      emailModalIsOpen: false,
      apiUrl: API_URL,
    };
  },
  computed: {
    authMechanismsLoaded() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms != null;
    },
    showGitHub() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.github ?? false;
    },
    showORCID() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.orcid ?? false;
    },
    showGoogle() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.google ?? false;
    },
    showMicrosoft() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.microsoft ?? false;
    },
    showEmail() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.email ?? false;
    },
    showUnsafeTestingPasswordlessLogin() {
      return (
        this.$store.state.serverInfo?.features?.auth_mechanisms
          ?.unsafe_testing_passwordless_login ?? false
      );
    },
  },
  methods: {
    loginUrl(provider) {
      const query = this.next ? `?next=${encodeURIComponent(this.next)}` : "";
      return `${this.apiUrl}/login/${provider}${query}`;
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

.orcid-icon {
  color: #a6ce39;
}
</style>
