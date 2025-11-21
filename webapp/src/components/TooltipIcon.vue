<template>
  <StyledTooltip :delay="500">
    <template #anchor>
      <font-awesome-icon :icon="['fas', 'info-circle']" class="info-icon" tabindex="0" />
    </template>
    <template #content>
      <slot>{{ text }}</slot>
    </template>
  </StyledTooltip>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";

export default {
  name: "TooltipIcon",
  components: {
    StyledTooltip,
  },
  props: {
    text: {
      type: String,
      default: "",
    },
  },
};
</script>

<style scoped>
.info-icon {
  cursor: help;
  margin-left: 0.25rem;
}

.info-icon:hover {
  color: cornflowerblue;
}
</style>
