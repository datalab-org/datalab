<template>
  <span v-if="creators && creators.length > 0">
    <span v-for="(creator, index) in creators" :key="index">
      <template v-if="showBubble && creator">
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
      <span class="display-name" v-if="showNames && creator.display_name">
        {{ creator.display_name }}
        <span v-if="index !== creators.length - 1">,</span>
      </span>
    </span>
  </span>
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
    creators: {
      type: Array,
      required: true,
    },
    showNames: {
      type: Boolean,
      default: false,
    },
    showBubble: {
      type: Boolean,
      default: true,
    },
    size: {
      type: Number,
      default: 32,
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

<style>
.display-name {
  margin-left: 0.5em;
}
.avatar {
  border-radius: 50%;
  border: 2px solid grey;
  opacity: 1;
}
img {
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
