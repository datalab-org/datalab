<template>
  <div class="login-container">
    <div class="welcome-section">
      <h1 style="font-size: 4rem">Welcome to Datalab</h1>
      <p>datalab is a place to store experimental data and the connections between them.</p>
      <p>
        datalab is open source (MIT license) and development occurs on GitHub at
        <a href="https://github.com/datalab-org/datalab"
          ><font-awesome-icon :icon="['fab', 'github']" />&nbsp;datalab-org/datalab</a
        >
        with documentation available on
        <a href="https://the-datalab.readthedocs.io"
          ><font-awesome-icon icon="book" />&nbsp;ReadTheDocs</a
        >.
      </p>
      <router-link to="/about" class="btn btn-default">Learn More</router-link>
    </div>

    <div class="login-options">
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

      <!-- <pre style="white-space: pre-wrap">{{ ASCII }}</pre> -->
      <div class="login-button">
        <a
          type="button"
          :class="{ disabled: !showGitHub }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via GitHub"
          :href="apiUrl + '/login/github'"
        >
          <font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub
        </a>
        <a
          type="button"
          :class="{ disabled: !showORCID }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via ORCID"
          :href="apiUrl + '/login/orcid'"
        >
          <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID
        </a>
        <a
          type="button"
          :class="{ disabled: !showEmail }"
          class="btn btn-default btn-login p-3"
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
  flex-direction: row;
  height: 100vh;
}

.welcome-section {
  flex: 1;
  gap: 1.5em;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  align-items: center;
  background-color: lightblue;
}

.login-options {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
}

.login-button {
  display: flex;
  flex-direction: column;
  width: 50%;
  gap: 2em;
}

.logo-container {
  position: fixed;
  top: 0;
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

.btn-login {
  font-size: 1.3rem;
}

a > .logo-banner:hover {
  filter: alpha(opacity=40);
  opacity: 0.4;
}

.orcid-icon {
  color: #a6ce39;
}
</style>
