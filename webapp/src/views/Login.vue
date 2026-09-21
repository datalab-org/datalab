<template>
  <div class="login-page">
    <div class="login-box">
      <div v-if="logo_url != null" class="logo-container">
        <a
          v-if="homepage_url != null"
          :href="homepage_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img class="logo-banner" :src="logo_url" />
        </a>
        <img v-else class="logo-banner" :src="logo_url" />
      </div>

      <div class="login-info">
        <LoginInfo>
          <template #login>
            <div v-if="!isLoaded" class="text-muted text-center">
              <font-awesome-icon icon="spinner" spin /> Loading...
            </div>

            <div v-else-if="currentUser != null" class="login-buttons text-center">
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

            <div v-else class="login-buttons">
              <div v-if="noAuthMechanismsAvailable" class="text-muted text-center">
                No login methods are currently available. Please contact the admin of this datalab
                server.
              </div>
              <div v-else class="dropdown align-self-center">
                <button
                  id="loginDropdown"
                  class="btn btn-default dropdown-toggle"
                  type="button"
                  aria-haspopup="true"
                  :aria-expanded="isLoginDropdownVisible"
                  @click="isLoginDropdownVisible = !isLoginDropdownVisible"
                >
                  <font-awesome-icon icon="sign-in-alt" />&nbsp;Login/Register
                </button>
                <div
                  v-show="isLoginDropdownVisible"
                  class="dropdown-menu"
                  style="display: block"
                  aria-labelledby="loginDropdown"
                >
                  <LoginDropdown :next="nextPath" />
                </div>
              </div>
            </div>
          </template>
        </LoginInfo>
      </div>
    </div>
  </div>
</template>

<script>
import LoginInfo from "@/components/LoginInfo.vue";
import LoginDropdown from "@/components/LoginDropdown.vue";
import { getInfo } from "@/server_fetch_utils.js";
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";

export default {
  components: {
    LoginInfo,
    LoginDropdown,
  },
  data() {
    return {
      isLoginDropdownVisible: false,
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      authMechanisms: {},
      currentUser: null,
      isLoaded: false,
    };
  },
  computed: {
    noAuthMechanismsAvailable() {
      return !Object.values(this.authMechanisms).some(Boolean);
    },
    currentUserDisplayName() {
      return this.currentUser?.display_name || this.currentUser?.contact_email || "this account";
    },
    nextPath() {
      const next = Array.isArray(this.$route.query.next)
        ? this.$route.query.next[0]
        : this.$route.query.next;
      return typeof next === "string" ? next : null;
    },
  },
  async mounted() {
    let info;
    [this.currentUser, info] = await Promise.all([
      this.$store.dispatch("fetchCurrentUser", { fullInfo: true }),
      getInfo().catch(() => null),
    ]);
    this.authMechanisms = info?.features?.auth_mechanisms ?? {};
    this.isLoaded = true;
  },
  methods: {
    goToApp() {
      const next = this.nextPath;
      const isLocalPath =
        next != null && next.startsWith("/") && !next.startsWith("//") && !next.includes("\\");
      // Full page load so that App.vue runs the startup fetches it skips on the login route
      window.location.href = this.$router.resolve(isLocalPath ? next : { name: "samples" }).href;
    },
  },
};
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  min-height: 100vh;
  padding: 2rem 1rem;
  background-color: var(--login-background, transparent);
}

.logo-container {
  display: flex;
  justify-content: center;
}

.logo-banner {
  display: block;
  width: 100%;
  max-width: var(--login-logo-max-width, 400px);
  max-height: var(--login-logo-max-height, 200px);
  object-fit: contain;
}

a > .logo-banner:hover {
  opacity: 0.6;
}

.login-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
  max-width: var(--login-max-width, 1080px);
  padding: 2rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: var(--login-box-background, #fff);
  color: var(--login-box-color, inherit);
}

.login-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
  text-align: center;
}

.login-buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: min(100%, 24rem);
}

.btn-login {
  font-size: 1.3rem;
}

.logged-in-title {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}
</style>
