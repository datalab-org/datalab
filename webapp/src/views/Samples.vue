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
    <div v-else class="btn btn-default mx-auto">
      <a :href="this.apiUrl + '/login/github'">Login</a>
    </div>
  </div>
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto mb-3">
        <button class="btn btn-default" @click="modalIsOpen = true">Add a sample</button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <SampleTable></SampleTable>
      </div>
    </div>
  </div>
  <CreateSampleModal v-model="modalIsOpen" />
</template>

<script>
import SampleTable from "@/components/SampleTable.vue";
import CreateSampleModal from "@/components/CreateSampleModal";
import { getUserInfo } from "@/server_fetch_utils.js";
import { API_URL } from "@/resources.js";

export default {
  name: "Samples",
  data() {
    return {
      modalIsOpen: false,
      loginModalIsOpen: false,
      apiUrl: API_URL,
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
  components: {
    SampleTable,
    CreateSampleModal,
  },
  mounted() {
    this.getUser();
  },
};
</script>

<style scoped>
.fade {
  opacity: 0;
  transition: opacity 0.15s linear;
}
.fade.show {
  opacity: 1;
}

#tableContainer.overlay:after {
  content: "";
  display: block;
  position: fixed; /* could also be absolute */
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.2);
}
</style>
