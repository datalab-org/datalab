<template>
  <div class="pt-3" v-if="this.logo_url != null">
    <a v-if="this.homepage_url != null" :href="this.homepage_url" target="_blank">
      <img class="logo-banner" :src="this.logo_url" />
    </a>
    <img v-else class="logo-banner" :src="this.logo_url" />
  </div>

  <LoginDetails></LoginDetails>

  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/collections">Collections</router-link> |
    <router-link to="/starting-materials">Inventory</router-link> |
    <span v-if="user && user.role === 'admin'"><router-link to="/admin">Admin</router-link> |</span>
    <router-link to="/item-graph"
      ><font-awesome-icon icon="project-diagram" />&nbsp;Graph View</router-link
    >
  </div>
</template>

<script>
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";
import LoginDetails from "@/components/LoginDetails.vue";
import { getUserInfo } from "@/server_fetch_utils.js";

export default {
  name: "Navbar",
  data() {
    return {
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      user: null,
    };
  },
  components: {
    LoginDetails,
  },
  async mounted() {
    this.getUser();
  },
  methods: {
    async getUser() {
      const user = await getUserInfo();
      if (user !== null) {
        this.user = user;
      }
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
