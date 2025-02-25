<template>
  <div class="login-container">
    <div class="background-animation"></div>

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
      <h1>Welcome to Datalab</h1>
      <p class="description">Choose your preferred login method to get started.</p>

      <div class="login-cards">
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

    <GetEmailModal v-model="emailModalIsOpen" />
  </div>
</template>

<script>
import GetEmailModal from "@/components/GetEmailModal.vue";
import { API_URL, LOGO_URL } from "@/resources.js";

export default {
  components: {
    GetEmailModal,
  },
  data() {
    return {
      emailModalIsOpen: false,
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      hoverGitHub: false,
      hoverORCID: false,
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
.login-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #6e45e2, #88d3ce);
}

.background-animation {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, #6e45e2, #88d3ce);
  animation: gradientShift 10s ease infinite;
  z-index: -1;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.logo-container {
  position: fixed;
  top: 0;
  text-align: center;
  overflow: hidden;
  background: white;
  border-radius: 15px;
  border: 1px solid lightgray;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
  padding-left: 1em;
  padding-right: 1em;
  margin-top: 1em;
}

.logo-banner {
  max-width: 150px;
  background: transparent !important;
}

.login-box {
  margin-top: 2rem;
  text-align: center;
}

.description {
  font-size: 1.5rem;
  color: white;
  margin-bottom: 2rem;
}

.login-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  justify-content: center;
}

.login-card {
  width: 200px;
  padding: 1.5rem;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
  text-align: center;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
  cursor: pointer;
}

.login-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.6);
}

.login-card a {
  display: block;
  margin-top: 1rem;
  font-size: 1rem;
  color: white;
  text-decoration: none;
}

.orcid-icon {
  color: #a6ce39;
}

h1 {
  font-size: 5em;
}
</style>
