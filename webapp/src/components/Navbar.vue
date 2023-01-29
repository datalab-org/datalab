<template>
  <div v-if="this.logo_url != null">
    <a v-if="this.homepage_url != null" :href="this.homepage_url" target="_blank">
      <img class="logo-banner" :src="this.logo_url" />
    </a>
    <img v-else class="logo-banner" :src="this.logo_url" />
  </div>
  <div class="row justify-content-center">
    <div v-if="currentUser != null">
      <b>{{ currentUser }}&nbsp;&nbsp;</b>
      <img
        :src="
          'https://www.gravatar.com/avatar/' +
          md5(this.currentUserInfo.contact_email || this.currentUserInfo.display_name) +
          '?s=36&d=' +
          this.gravatar_style
        "
        class="avatar"
        width="36"
        height="36"
        :title="this.currentUserInfo.display_name"
      />
      &nbsp;&nbsp;<a :href="this.apiUrl + '/logout'" class="btn btn-default btn-link text-primary"
        >Logout</a
      >
    </div>
    <div v-else class="btn btn-default">
      <a :href="this.apiUrl + '/login/github'">Login</a>
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
import { API_URL, LOGO_URL, HOMEPAGE_URL, GRAVATAR_STYLE } from "@/resources.js";
import { getUserInfo } from "@/server_fetch_utils.js";
import crypto from "crypto";

export default {
  name: "Navbar",
  data() {
    return {
      apiUrl: API_URL,
      logo_url: LOGO_URL,
      homepage_url: HOMEPAGE_URL,
      loginModalIsOpen: false,
      gravatar_style: GRAVATAR_STYLE,
      currentUser: null,
      currentUserInfo: {},
    };
  },
  methods: {
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.currentUser = user.display_name;
        this.currentUserInfo = {
          display_name: user.display_name || "",
          immutable_id: user.immutable_id,
          contact_email: user.contact_email || "",
        };
        console.log(this.currentUser, this.currentUserInfo);
      }
    },
    md5(value) {
      // Returns the MD5 hash of the given string.
      return crypto.createHash("md5").update(value).digest("hex");
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

.avatar {
  border: 2px solid skyblue;
  border-radius: 50%;
}
.avatar:hover {
  border: 2px solid grey;
}
</style>
