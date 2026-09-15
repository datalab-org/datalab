<template>
  <div class="login-container">
    <div class="welcome-section">
      <LoginInfo />
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
          rel="noopener noreferrer"
        >
          <img class="logo-banner" :src="logo_url" />
        </a>
        <img v-else class="logo-banner" :src="logo_url" />
      </div>

      <div v-if="!isLoaded" class="text-muted text-center">
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
          v-for="provider in visibleOAuthProviders"
          :key="provider.name"
          :class="{ disabled: !authMechanismEnabled(provider.name) }"
          class="btn btn-default btn-login p-3"
          :aria-label="`Login via ${provider.label}`"
          :aria-disabled="!authMechanismEnabled(provider.name)"
          :href="authMechanismEnabled(provider.name) ? oauthLoginUrl(provider.name) : null"
        >
          <font-awesome-icon
            :class="{ 'orcid-icon': provider.name === 'orcid' }"
            :icon="provider.icon"
          />
          Login via {{ provider.label }}
        </a>
        <button
          v-if="shouldShowAuthMechanism('email')"
          type="button"
          class="btn btn-default btn-login p-3"
          aria-label="Login via email"
          :disabled="!authMechanismEnabled('email')"
          @click="emailModalIsOpen = true"
        >
          <font-awesome-icon :icon="['fa', 'envelope']" /> Login via email
        </button>
        <div v-if="noAuthMechanismsAvailable" class="text-muted text-center">
          No login methods are currently available. Please contact the admin of this datalab server.
        </div>
      </div>
    </div>
  </div>
  <GetEmailModal v-model="emailModalIsOpen" />
</template>

<script>
import LoginInfo from "@/components/LoginInfo.vue";
import GetEmailModal from "@/components/GetEmailModal.vue";
import { getAuthMechanisms } from "@/server_fetch_utils.js";
import { API_URL, LOGO_URL, HOMEPAGE_URL, LOGIN_HIDE_UNAVAILABLE_AUTH } from "@/resources.js";

const OAUTH_PROVIDERS = [
  { name: "github", label: "GitHub", icon: ["fab", "github"] },
  { name: "orcid", label: "ORCID", icon: ["fab", "orcid"] },
  { name: "google", label: "Google", icon: ["fab", "google"] },
  { name: "microsoft", label: "Microsoft", icon: ["fab", "microsoft"] },
];

export default {
  components: {
    LoginInfo,
    GetEmailModal,
  },
  data() {
    return {
      emailModalIsOpen: false,
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      authMechanisms: {},
      currentUser: null,
      isLoaded: false,
    };
  },
  computed: {
    visibleOAuthProviders() {
      return OAUTH_PROVIDERS.filter(({ name }) => this.shouldShowAuthMechanism(name));
    },
    noAuthMechanismsAvailable() {
      return !Object.values(this.authMechanisms).some(Boolean);
    },
    currentUserDisplayName() {
      return this.currentUser?.display_name || this.currentUser?.contact_email || "this account";
    },
  },
  async mounted() {
    [this.currentUser, this.authMechanisms] = await Promise.all([
      this.$store.dispatch("fetchCurrentUser", { fullInfo: true }),
      getAuthMechanisms().catch(() => ({})),
    ]);
    this.isLoaded = true;
  },
  methods: {
    authMechanismEnabled(name) {
      return this.authMechanisms[name] ?? false;
    },
    shouldShowAuthMechanism(name) {
      return !LOGIN_HIDE_UNAVAILABLE_AUTH || this.authMechanismEnabled(name);
    },
    oauthLoginUrl(provider) {
      const next = Array.isArray(this.$route.query.next)
        ? this.$route.query.next[0]
        : this.$route.query.next;
      const query = typeof next === "string" ? `?next=${encodeURIComponent(next)}` : "";
      return `${this.apiUrl}/login/${provider}${query}`;
    },
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

@media (max-width: 767.98px) {
  .login-container {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
  }

  .welcome-section,
  .login-options {
    flex: none;
    min-height: 50vh;
  }

  .login-button {
    width: min(100%, 20rem);
  }

  .logo-container {
    position: static;
  }
}
</style>
