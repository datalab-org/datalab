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
    :href="apiUrl + '/login/github'"
    ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
  >
  <a
    v-if="showORCID"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via ORCID"
    :href="apiUrl + '/login/orcid'"
    ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID</a
  >
  <a
    v-if="showGoogle"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via Google"
    :href="apiUrl + '/login/google'"
    ><font-awesome-icon :icon="['fab', 'google']" /> Login via Google</a
  >
  <a
    v-if="showMicrosoft"
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Login via Microsoft"
    :href="apiUrl + '/login/microsoft'"
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
</template>

<script>
import GetEmailModal from "@/components/GetEmailModal.vue";
import { API_URL } from "@/resources.js";

export default {
  components: {
    GetEmailModal,
  },
  props: {
    modelValue: Boolean,
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
