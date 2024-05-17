<template>
  <img
    :src="
      'https://www.gravatar.com/avatar/' +
      md5(this.creator.contact_email || this.creator.display_name) +
      '?d=' +
      this.gravatar_style +
      '&s=' +
      size
    "
    class="avatar"
    :width="size"
    :height="size"
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
      type: Number,
      default: 32,
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
  border: 2px solid grey;
  opacity: 1;
}
.avatar:hover {
  border: 2px solid black;
  transition: border 0.25s ease;
  box-shadow: 0 0 5px 0 skyblue;
}
</style>
