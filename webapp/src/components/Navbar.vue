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
      <img class="logo-banner" :src="logo_url" />
    </a>
    <img v-else class="logo-banner" :src="logo_url" />
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
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";
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
      homepage_url: HOMEPAGE_URL,
      user: null,
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
  methods: {
    disableSuperUserMode() {
      this.$store.commit("setAdminSuperUserMode", false);
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.logo-banner {
  max-width: 200px;
  width: 100px;
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
