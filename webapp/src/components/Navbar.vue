<template>
  <div class="pt-3" v-if="logoURL != null">
    <a v-if="homepageURL != null" :href="homepageURL.value" target="_blank">
      <img class="logo-banner" :alt="logoURL.description" :src="logoURL.value" />
    </a>
    <img v-else class="logo-banner" :alt="logoURL.description" :src="logoURL.value" />
  </div>

  <LoginDetails></LoginDetails>

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
</template>

<script>
import LoginDetails from "@/components/LoginDetails.vue";
import { getPublicSettingsList } from "@/server_fetch_utils.js";

export default {
  name: "Navbar",
  computed: {
    publicSettings() {
      return this.$store.getters.getPublicSettings;
    },
    logoURL() {
      const logoURL = this.publicSettings.find((setting) => setting.name === "LOGO_URL");
      return logoURL ? logoURL : null;
    },
    homepageURL() {
      const homepageURL = this.publicSettings.find((setting) => setting.name === "HOMEPAGE_URL");
      return homepageURL ? homepageURL : null;
    },
  },
  components: {
    LoginDetails,
  },
  methods: {
    async getPublicSettings() {
      await getPublicSettingsList();
    },
  },
  mounted() {
    this.getPublicSettings();
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
