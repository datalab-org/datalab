<template>
  <h1 style="font-size: 2.5rem">
    Welcome to
    <i v-if="websiteTitle === 'datalab'">datalab</i>
    <template v-else>the {{ websiteTitle }}</template>
  </h1>
  <slot name="login" />
  <a
    v-if="homepageUrl != null"
    :href="homepageUrl"
    class="btn btn-default"
    target="_blank"
    rel="noopener noreferrer"
  >
    <font-awesome-icon icon="home" /> Homepage
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
