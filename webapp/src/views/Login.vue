<!-- This file was edited with the assistance of an AI model and requires human review from the contributor. -->
<template>
  <div class="login-container">
    <div class="welcome-section">
      <CustomLoginInfo v-if="customLoginInfoHasContent" />
      <LoginInfo v-else />
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

      <div v-if="!userInfoLoaded" class="text-muted text-center">
        <font-awesome-icon icon="spinner" spin /> Loading...
      </div>

      <div v-else-if="currentUser != null" class="login-button logged-in-options text-center">
        <div>
          <h2 class="logged-in-title">You are already logged in</h2>
          <p class="text-muted mb-0">
            Signed in as <strong>{{ currentUserDisplayName }}</strong>
          </p>
        </div>
        <button type="button" class="btn btn-default btn-login p-3" @click="goToApp">
          <font-awesome-icon icon="home" /> Go to app
        </button>
        <a type="button" class="btn btn-default btn-login p-3" :href="apiUrl + '/logout'">
          <font-awesome-icon icon="sign-out-alt" /> Logout
        </a>
      </div>

      <div v-else class="login-button">
        <a
          v-if="showUnavailableAuthMechanisms || showGitHub"
          type="button"
          :class="{ disabled: !showGitHub }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via GitHub"
          :href="apiUrl + '/login/github'"
        >
          <font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub
        </a>
        <a
          v-if="showUnavailableAuthMechanisms || showORCID"
          type="button"
          :class="{ disabled: !showORCID }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via ORCID"
          :href="apiUrl + '/login/orcid'"
        >
          <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID
        </a>
        <a
          v-if="showUnavailableAuthMechanisms || showGoogle"
          type="button"
          :class="{ disabled: !showGoogle }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via Google"
          :href="apiUrl + '/login/google'"
        >
          <font-awesome-icon :icon="['fab', 'google']" /> Login via Google
        </a>
        <a
          v-if="showUnavailableAuthMechanisms || showMicrosoft"
          type="button"
          :class="{ disabled: !showMicrosoft }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via Microsoft"
          :href="apiUrl + '/login/microsoft'"
        >
          <font-awesome-icon :icon="['fab', 'microsoft']" /> Login via Microsoft
        </a>
        <a
          v-if="showUnavailableAuthMechanisms || showEmail"
          type="button"
          :class="{ disabled: !showEmail }"
          class="btn btn-default btn-login p-3"
          aria-label="Login via email"
          @click="emailModalIsOpen = true"
        >
          <font-awesome-icon :icon="['fa', 'envelope']" /> Login via email
        </a>
        <div v-if="noAuthMechanismsAvailable" class="text-muted text-center">
          No login methods are currently available. Please contact the admin of this datalab server.
        </div>
      </div>
    </div>
  </div>
  <GetEmailModal v-model="emailModalIsOpen" />
</template>

<script>
import CustomLoginInfo from "@/components/CustomLoginInfo.vue";
import LoginInfo from "@/components/LoginInfo.vue";
import GetEmailModal from "@/components/GetEmailModal.vue";
import { getAuthMechanisms, getUserInfo } from "@/server_fetch_utils.js";
import { API_URL, LOGO_URL, HOMEPAGE_URL, LOGIN_HIDE_UNAVAILABLE_AUTH } from "@/resources.js";

export default {
  components: {
    CustomLoginInfo,
    LoginInfo,
    GetEmailModal,
  },
  data() {
    return {
      emailModalIsOpen: false,
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      authMechanisms: null,
      currentUser: null,
      userInfoLoaded: false,
    };
  },
  computed: {
    customLoginInfoHasContent() {
      return CustomLoginInfo.hasContent !== false;
    },
    showUnavailableAuthMechanisms() {
      return !LOGIN_HIDE_UNAVAILABLE_AUTH;
    },
    showGitHub() {
      return this.authMechanisms?.github ?? false;
    },
    showORCID() {
      return this.authMechanisms?.orcid ?? false;
    },
    showGoogle() {
      return this.authMechanisms?.google ?? false;
    },
    showMicrosoft() {
      return this.authMechanisms?.microsoft ?? false;
    },
    showEmail() {
      return this.authMechanisms?.email ?? false;
    },
    noAuthMechanismsAvailable() {
      return this.authMechanisms != null && !Object.values(this.authMechanisms).some(Boolean);
    },
    currentUserDisplayName() {
      return (
        this.currentUser?.display_name ||
        this.currentUser?.name ||
        this.currentUser?.email ||
        "this account"
      );
    },
  },
  async mounted() {
    try {
      this.currentUser = await getUserInfo();
    } finally {
      this.userInfoLoaded = true;
    }

    try {
      this.authMechanisms = await getAuthMechanisms();
    } catch {
      this.authMechanisms = {};
    }
  },
  methods: {
    goToApp() {
      window.location.href = "/samples";
    },
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
  background-color: var(--login-welcome-background, lightblue);
  color: var(--login-welcome-color, inherit);
}

.login-options {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
  background-color: var(--login-options-background, transparent);
  color: var(--login-options-color, inherit);
}

.login-button {
  display: flex;
  flex-direction: column;
  width: 50%;
  gap: 2em;
}

.logged-in-options {
  gap: 1.25rem;
}

.logged-in-title {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
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
