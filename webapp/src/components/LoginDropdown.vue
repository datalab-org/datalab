<template>
  <GetEmailModal v-model="emailModalIsOpen" />
  <a
    type="button"
    :class="{ disabled: !showGitHub }"
    class="dropdown-item btn login btn-link"
    aria-label="Login via GitHub"
    :href="apiUrl + '/login/github'"
    ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
  >
  <a
    type="button"
    :class="{ disabled: !showORCID }"
    class="dropdown-item btn login btn-link"
    aria-label="Login via ORCID"
    :href="apiUrl + '/login/orcid'"
    ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID</a
  >
  <button
    type="button"
    :class="{ disabled: !showEmail }"
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
    showGitHub() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.github ?? false;
    },
    showORCID() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.orcid ?? false;
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
