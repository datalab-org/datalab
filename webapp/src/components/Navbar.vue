<template>
  <div
    v-if="logo_url != null"
    class="pt-3"
    style="display: flex; justify-content: center; align-items: center"
  >
    <a
      v-if="homepage_url != null"
      :href="homepage_url"
      style="display: inline-block"
      target="_blank"
    >
      <img class="logo-banner" :width="logo_width + 'px'" :src="logo_url" />
    </a>
    <img v-else class="logo-banner" :width="logo_width + 'px'" :src="logo_url" />
  </div>

  <div
    class="container d-flex flex-column align-items-center pt-3"
    data-testid="navbar-logindetails"
  >
    <LoginDetails />
  </div>

  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/collections">Collections</router-link> |
    <router-link to="/starting-materials">Inventory</router-link> |
    <router-link to="/equipment">Equipment</router-link> |
    <router-link to="/item-graph"
      ><font-awesome-icon icon="project-diagram" />&nbsp;Graph View</router-link
    >
    |
    <span ref="analysisMenu" class="nav-dropdown">
      <a
        href="#"
        class="nav-dropdown-toggle"
        :class="{ active: analysisMenuOpen }"
        @click.prevent="analysisMenuOpen = !analysisMenuOpen"
        ><font-awesome-icon icon="flask" />&nbsp;Analysis tools&nbsp;<font-awesome-icon
          icon="caret-down"
      /></a>
      <div v-show="analysisMenuOpen" class="nav-dropdown-menu">
        <router-link to="/compare" class="nav-dropdown-item" @click="analysisMenuOpen = false">
          <font-awesome-icon icon="layer-group" fixed-width />&nbsp;Sample comparison
        </router-link>
      </div>
    </span>
  </div>
  <div v-if="!isLoggedIn" class="container">
    <div class="alert alert-info col-md-6 col-lg-4 text-center mx-auto info-banner">
      <div class="info-banner-text">
        <font-awesome-icon icon="info-circle" fixed-width /> Please login to view or create items.
      </div>
    </div>
  </div>
  <div v-if="adminSuperUserMode" class="container">
    <div class="alert alert-warning col-md-8 col-lg-8 text-center mx-auto super-user-banner">
      <div class="super-user-banner-text">
        <font-awesome-icon icon="exclamation-triangle" fixed-width /> Super-user mode is currently
        active. You have read access to all items.
        <div>
          <a href="#" class="disable-link" @click.prevent="disableSuperUserMode">(disable)</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_URL, LOGO_URL, LOGO_WIDTH, HOMEPAGE_URL } from "@/resources.js";
import LoginDetails from "@/components/LoginDetails.vue";

export default {
  name: "Navbar",
  components: {
    LoginDetails,
  },
  data() {
    return {
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      logo_width: LOGO_WIDTH,
      homepage_url: HOMEPAGE_URL,
      user: null,
      analysisMenuOpen: false,
    };
  },
  computed: {
    isLoggedIn() {
      return Boolean(this.$store.state.currentUserDisplayName);
    },
    adminSuperUserMode() {
      return this.$store.getters.isAdminSuperUserModeActive;
    },
  },
  mounted() {
    document.addEventListener("click", this.handleClickOutside);
  },
  unmounted() {
    document.removeEventListener("click", this.handleClickOutside);
  },
  methods: {
    handleClickOutside(event) {
      if (this.analysisMenuOpen && !this.$refs.analysisMenu?.contains(event.target)) {
        this.analysisMenuOpen = false;
      }
    },
    disableSuperUserMode() {
      this.$store.commit("setAdminSuperUserMode", false);
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.nav-dropdown {
  position: relative;
  display: inline-block;
}
.nav-dropdown-toggle {
  cursor: pointer;
  color: #2c3e50;
  font-weight: bold;
}
.nav-dropdown-toggle:hover,
.nav-dropdown-toggle.active {
  color: #42b983;
}
.nav-dropdown-menu {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: 100%;
  margin-top: 0.35rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 0.35rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  min-width: 12rem;
  padding: 0.25rem 0;
}
.nav-dropdown-item {
  display: block;
  padding: 0.4rem 1rem;
  white-space: nowrap;
  text-align: left;
  color: #2c3e50 !important;
  font-weight: normal;
}
.nav-dropdown-item:hover {
  background-color: #f3f6f4;
  color: #42b983 !important;
}

.logo-banner {
  max-width: 200px;
  display: block;
  margin-left: auto;
  margin-right: auto;
  filter: alpha(opacity=100);
  opacity: 1;
}
a > .logo-banner:hover {
  filter: alpha(opacity=40);
  opacity: 0.4;
}

.info-banner {
  background-color: white;
  border-color: #007bff;
  color: #004085;
  background: repeating-linear-gradient(
    45deg,
    #004085,
    #004085 1px,
    transparent 1px,
    transparent 10px
  );
}

.info-banner-text {
  background-color: white;
  display: inline-block;
  padding: 0.25rem 0.5rem;
}

.super-user-banner {
  background-color: white;
  background: repeating-linear-gradient(
    45deg,
    #a52a2a,
    #a52a2a 1px,
    transparent 1px,
    transparent 10px
  );
  border-color: #a52a2a;
  color: #721c24;
}

.super-user-banner-text {
  background-color: white;
  display: inline-block;
  padding: 0.25rem 0.5rem;
}

.super-user-banner .disable-link {
  color: #721c24;
  text-decoration: underline;
}

.super-user-banner .disable-link:hover {
  color: #721c24;
}
</style>
