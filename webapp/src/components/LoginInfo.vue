<template>
  <h1 class="h4 font-weight-bold mb-1">
    Welcome to
    <template v-if="websiteTitle === 'datalab'"><br /><i>datalab</i></template>
    <template v-else>the<br />{{ websiteTitle }}</template>
  </h1>
  <p class="text-muted mb-4">Sign in or register to continue.</p>
  <slot name="login" />
  <a
    v-if="homepageUrl != null"
    :href="homepageUrl"
    class="btn btn-default mt-3"
    target="_blank"
    rel="noopener noreferrer"
  >
    <font-awesome-icon icon="home" /> Visit homepage
  </a>
</template>

<script>
import { WEBSITE_TITLE, HOMEPAGE_URL } from "@/resources.js";

export default {
  name: "LoginInfo",
  data() {
    return {
      websiteTitle: WEBSITE_TITLE,
      homepageUrl: HOMEPAGE_URL,
    };
  },
};
</script>
