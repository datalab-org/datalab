<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link> |
    <router-link to="/item-graph">Item graph</router-link>
    <div v-if="currentUser != null" class="btn mx-auto normal">
      <b>{{ currentUser }}</b> <i>({{ currentUserID }})</i>
      <a :href="this.apiUrl + '/logout'" class="btn-link mx-auto text-primary"> (Logout)</a>
    </div>
    <div v-else class="btn btn-default ml-3">
      <a :href="this.apiUrl + '/login/github'">Login</a>
    </div>
  </div>
</template>

<script>
import { API_URL } from "@/resources.js";

import { getUserInfo } from "@/server_fetch_utils.js";

export default {
  name: "Navbar",
  data() {
    return {
      apiUrl: API_URL,
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
