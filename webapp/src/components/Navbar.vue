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
    <router-link to="/equipment">Equipment</router-link> |

    <router-link to="/item-graph"
      ><font-awesome-icon icon="project-diagram" />&nbsp;Graph View</router-link
    >
  </div>
  <div class="container mt-2">
    <div class="mx-auto text-center alert alert-primary pb-1" role="alert">
      <p class="pb-0">
        This is the public demo deployment of datalab. Data may be removed at any time.
      </p>
      <p class="pb-0">
        If you wish to deploy your own instance you can find instructions and contact details for assistance on the <a href="https://github.com/the-grey-group/datalab">GitHub repository</a>.
      </p>
    </div>
  </div>
</template>

<script>
import { API_URL, LOGO_URL, HOMEPAGE_URL } from "@/resources.js";
import LoginDetails from "@/components/LoginDetails.vue";

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
