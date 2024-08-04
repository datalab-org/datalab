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

  <div class="row justify-content-center pt-3">
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
    <div class="alert alert-info col-md-6 col-lg-4 text-center mx-auto">
      Please login to view or create items.
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
</style>
