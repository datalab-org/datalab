<template>
  <div class="bubble-wrapper">
    <NotificationDot />
    <img
      :src="
        'https://www.gravatar.com/avatar/' +
        md5(creator.contact_email || creator.display_name) +
        '?d=' +
        gravatar_style
      "
      class="avatar"
      :width="size"
      :height="size"
      :title="creator.display_name"
    />
  </div>
</template>

<script>
import { GRAVATAR_STYLE } from "@/resources.js";

import NotificationDot from "./NotificationDot.vue";

import { getUsersList } from "@/server_fetch_utils.js";
import { md5 } from "js-md5";

export default {
  components: {
    NotificationDot,
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
  data() {
    return {
      gravatar_style: GRAVATAR_STYLE,
    };
  },
  computed: {
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
  },
  created() {
    if (this.creator.role == "admin") {
      getUsersList();
    }
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
  position: relative;
  border-radius: 50%;
  border: 2px solid grey;
  opacity: 1;
}
.avatar:hover {
  border: 2px solid black;
  transition: border 0.25s ease;
  box-shadow: 0 0 5px 0 skyblue;
}

.bubble-wrapper {
  position: relative;
  display: inline-block;
}
</style>
