<template>
  <img
    :src="
      'https://www.gravatar.com/avatar/' +
      md5(creator.contact_email || creator.display_name) +
      '?d=' +
      gravatar_style +
      '&s=' +
      size
    "
    class="avatar"
    :width="size"
    :height="size"
    :title="creator.display_name"
  />
</template>

<script>
import { md5 } from "js-md5";
import { GRAVATAR_STYLE } from "@/resources.js";
export default {
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
  data() {
    return {
      gravatar_style: GRAVATAR_STYLE,
    };
  },
  methods: {
    md5(value) {
      // Returns the MD5 hash of the given string.
      return md5(value);
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
