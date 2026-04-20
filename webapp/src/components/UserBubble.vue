<template>
  <StyledTooltip :delay="500">
    <template #anchor>
      <img
        :src="
          'https://www.gravatar.com/avatar/' +
          (creator.gravatar_hash || '') +
          '?d=' +
          gravatar_style +
          '&s=' +
          size
        "
        class="avatar"
        :width="size"
        :height="size"
      />
    </template>
    <template #content>
      {{ creator.display_name }}
    </template>
  </StyledTooltip>
</template>

<script>
import { GRAVATAR_STYLE } from "@/resources.js";
import StyledTooltip from "@/components/StyledTooltip";

export default {
  components: {
    StyledTooltip,
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
};
</script>

<style scoped>
.avatar {
  border-radius: 50%;
  border: 2px solid grey;
  opacity: 1;
  cursor: pointer;
}
.avatar:hover {
  border: 2px solid black;
  transition: border 0.25s ease;
  box-shadow: 0 0 5px 0 skyblue;
}
</style>
