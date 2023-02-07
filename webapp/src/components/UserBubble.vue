<template>
  <img
    :src="
      'https://www.gravatar.com/avatar/' +
      md5(this.creator.contact_email || this.creator.display_name) +
      '?s=' +
      this.size +
      '&d=' +
      this.gravatar_style
    "
    class="avatar"
    :width="this.size"
    :height="this.size"
    :title="this.creator.display_name"
  />
</template>

<script>
import crypto from "crypto";
import { GRAVATAR_STYLE } from "@/resources.js";
export default {
  data() {
    return {
      gravatar_style: GRAVATAR_STYLE,
    };
  },
  props: {
    creator: {
      type: Object,
      required: true,
    },
    size: {
      type: String,
      default: "32",
      required: false,
    },
  },
  methods: {
    md5(value) {
      // Returns the MD5 hash of the given string.
      return crypto.createHash("md5").update(value).digest("hex");
    },
  },
};
</script>
<style scoped>
.avatar {
  border-radius: 50%;
  border: 2px solid black;
  filter: alpha(opacity=100);
  opacity: 1;
}
.avatar:hover {
  opacity: 0.4;
}
</style>
