<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link>
    <div v-if="currentUser != null" class="btn mx-auto normal">
      <b>{{ currentUser }}</b> <i>({{ currentUserID }})</i>
      <a :href="this.api_url + '/logout'" class="btn-link mx-auto text-primary"> (Logout)</a>
    </div>
    <div v-else class="btn btn-default mx-auto">
      <a :href="this.api_url + '/login/github'">Login</a>
    </div>
    <router-link to="/item-graph">Item graph</router-link>
  </div>
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <StartingMaterialTable></StartingMaterialTable>
      </div>
    </div>
  </div>
</template>

<script>
import StartingMaterialTable from "@/components/StartingMaterialTable.vue";
import { getUserInfo } from "@/server_fetch_utils.js";
import { API_URL } from "@/resources.js";

export default {
  components: {
    StartingMaterialTable,
  },
  data() {
    return {
      currentUser: null,
      currentUserID: null,
      api_url: API_URL,
    };
  },
  methods: {
    async getUser() {
      let user = await getUserInfo();
      this.currentUser = user.display_name;
      this.currentUserID = user.immutable_id;
    },
  },
  mounted() {
    this.getUser();
  },
};
</script>
