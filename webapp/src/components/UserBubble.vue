<template>
  <StyledTooltip :delay="500">
    <template #anchor>
      <component
        :is="href ? 'a' : 'span'"
        :href="href"
        :target="href ? '_blank' : undefined"
        :rel="href ? 'noopener' : undefined"
        :aria-label="href ? linkLabel || creator.display_name : undefined"
        :class="{ 'avatar-link': href }"
      >
        <img
          :src="
            'https://www.gravatar.com/avatar/' +
            (creator.gravatar_hash || '') +
            '?d=' +
            gravatar_style +
            '&s=' +
            size
          "
          :alt="href ? '' : creator.display_name || ''"
          class="avatar"
          :width="size"
          :height="size"
        />
      </component>
    </template>
    <template #content>
      <slot name="tooltip">{{ creator.display_name }}</slot>
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
    href: {
      type: String,
      default: null,
    },
    // Accessible name for the link created by `href`; defaults to the creator's display name
    linkLabel: {
      type: String,
      default: null,
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
.avatar-link {
  display: inline-block;
  line-height: 0;
}

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
