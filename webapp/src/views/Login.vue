<template>
  <div class="login-page min-vh-100 px-3 py-5">
    <main class="login-box card shadow-sm mx-auto">
      <div class="card-body p-4 p-sm-5 text-center">
        <div v-if="logo_url" class="mb-4">
          <a v-if="homepage_url" :href="homepage_url" target="_blank" rel="noopener noreferrer">
            <img class="logo-banner d-block mx-auto" :src="logo_url" alt="Logo" />
          </a>
          <img v-else class="logo-banner d-block mx-auto" :src="logo_url" alt="Logo" />
        </div>

        <LoginInfo>
          <template #login>
            <div class="login-controls mx-auto">
              <div v-if="!isLoaded" class="text-muted">
                <font-awesome-icon icon="spinner" spin /> Loading...
              </div>

              <template v-else-if="currentUser != null">
                <p class="text-muted mb-3">
                  Signed in as <strong>{{ currentUserDisplayName }}</strong>
                </p>
                <button type="button" class="btn btn-default btn-block" @click="goToApp">
                  Continue to app
                </button>
                <a class="d-inline-block mt-3 small text-muted" :href="apiUrl + '/logout'">
                  <font-awesome-icon icon="sign-out-alt" /> Log out
                </a>
              </template>

              <p v-else-if="noAuthMechanismsAvailable" class="text-muted mb-0">
                No login methods are currently available. Please contact the admin of this datalab
                server.
              </p>

              <div
                v-else
                v-on-click-outside="() => (isLoginDropdownVisible = false)"
                class="dropdown d-inline-block"
              >
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
                  <LoginDropdown :next="nextPath" :remember="rememberMe" />
                </div>
                <div class="form-check mt-3">
                  <input
                    id="rememberMe"
                    v-model="rememberMe"
                    type="checkbox"
                    class="form-check-input"
                    data-testid="remember-me-checkbox"
                  />
                  <label
                    class="form-check-label small text-muted"
                    for="rememberMe"
                    title="Remember me on this machine (do not use on shared machines)"
                  >
                    Remember me on this device
                  </label>
                </div>
              </div>
            </div>
          </template>
        </LoginInfo>
      </div>
    </main>
  </div>
</template>

<script>
import LoginInfo from "@/components/LoginInfo.vue";
import LoginDropdown from "@/components/LoginDropdown.vue";
import { getInfo } from "@/server_fetch_utils.js";
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";
import { vOnClickOutside } from "@vueuse/components";

export default {
  directives: {
    onClickOutside: vOnClickOutside,
  },
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
      rememberMe: false,
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
/* Only deployment-overridable values live here; layout uses Bootstrap utilities */
.login-page {
  background-color: var(--login-background, #f5f6f8);
}

.login-box {
  max-width: var(--login-max-width, 26rem);
  background: var(--login-box-background, #fff);
  color: var(--login-box-color, inherit);
}

.logo-banner {
  max-width: min(100%, var(--login-logo-max-width, 240px));
  max-height: var(--login-logo-max-height, 120px);
  object-fit: contain;
}

a > .logo-banner:hover {
  opacity: 0.7;
}

.login-controls {
  max-width: 16rem;
}
</style>
