<template>
  <div v-if="this.logo_url != null">
    <a v-if="this.homepage_url != null" :href="this.homepage_url" target="_blank">
      <img class="logo-banner" :src="this.logo_url" />
    </a>
    <img v-else class="logo-banner" :src="this.logo_url" />
  </div>
  <div class="row justify-content-center">
    <div v-if="currentUser != null">
      <b>{{ currentUser }}</b> <i>({{ currentUserID }})</i> &nbsp;<a
        :href="this.api_url + '/logout'"
        class="btn btn-default btn-link text-primary"
        >Logout</a
      >
    </div>
    <div v-else class="btn btn-default">
      <a :href="this.api_url + '/login/github'">Login</a>
    </div>
  </div>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link> |
    <router-link to="/item-graph">Item graph</router-link>
  </div>
</template>

<script>
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";
import { getUserInfo } from "@/server_fetch_utils.js";

export default {
  name: "Navbar",
  data() {
    return {
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      loginModalIsOpen: false,
      currentUser: null,
      currentUserID: null,
    };
  },
  methods: {
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.currentUser = user.display_name;
        this.currentUserID = user.immutable_id;
      }
    },
  },
  mounted() {
    this.getUser();
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
