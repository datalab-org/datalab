<template>
  <div class="login-container">
    <div
      v-if="logo_url != null"
      class="pt-3 logo-container"
      style="display: flex; justify-content: center; align-items: center"
    >
      <a
        v-if="homepage_url != null"
        :href="homepage_url"
        style="display: inline-block"
        target="_blank"
      >
        <img class="logo-banner" :src="logo_url" />
      </a>
      <img v-else class="logo-banner" :src="logo_url" />
    </div>
    <div class="login-box">
      <div class="ascii-section">
        <pre style="color: green; white-space: pre-wrap">{{ ASCII }}</pre>
      </div>
      <p class="description">
        Welcome to Datalab - Your place to store experimental data and the connections between them.
      </p>
      <div class="login-buttons">
        <a
          type="button"
          :class="{ disabled: !showGitHub }"
          class="btn btn-default btn-login pt-3"
          aria-label="Login via GitHub"
          :href="apiUrl + '/login/github'"
        >
          <font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub
        </a>
        <a
          type="button"
          :class="{ disabled: !showORCID }"
          class="btn btn-default btn-login pt-3"
          aria-label="Login via ORCID"
          :href="apiUrl + '/login/orcid'"
        >
          <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID
        </a>
        <a
          type="button"
          :class="{ disabled: !showEmail }"
          class="btn btn-default btn-login pt-3"
          aria-label="Login via email"
          @click="emailModalIsOpen = true"
        >
          <font-awesome-icon :icon="['fa', 'envelope']" /> Login via email
        </a>
      </div>
    </div>
  </div>
  <GetEmailModal v-model="emailModalIsOpen" />
</template>

<script>
import GetEmailModal from "@/components/GetEmailModal.vue";
import { getInfo } from "@/server_fetch_utils.js";
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";

export default {
  components: {
    GetEmailModal,
  },
  data() {
    return {
      emailModalIsOpen: false,
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      ASCII: `
              oooo              o8              o888             oooo
           ooooo888    ooooooo o888oo  ooooooo    888   ooooooo    888ooooo
         888    888    ooooo888 888    ooooo888   888   ooooo888   888    888
         888    888  888    888 888  888    888   888 888    888   888    888
           88ooo888o  88ooo88 8o 888o 88ooo88 8o o888o 88ooo88 8o o888ooo88
      `,
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
  async mounted() {
    getInfo();
  },
};
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  align-items: center;
  justify-content: center;
  gap: 2rem;
}

.logo-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
}

.ascii-section {
  text-align: center;
  display: flex;
  justify-content: center;
  white-space: pre-wrap;
  font-family: monospace;
  width: 100%;
  animation: fadeIn 3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.logo-banner {
  max-width: 200px;
  width: 100px;
  display: block;
  margin-left: auto;
  margin-right: auto;
  filter: alpha(opacity=100);
  opacity: 1;
}

.login-buttons {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
}

.btn-login {
  font-size: 1.3rem;
  width: 20%;
  text-align: center;
}

.orcid-icon {
  color: #a6ce39;
}

.description {
  font-size: 1.2rem;
  color: black;
  text-align: center;
  margin-top: 1rem;
}

.login-box {
  padding: 5rem;
  border-radius: 15px;
  border: 1px solid lightgray;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
  text-align: center;
  width: 100%;
  max-width: 75%;
}
</style>
