<template>
  <div ref="anchor" class="tooltip-anchor">
    <slot name="anchor"></slot>
  </div>
  <div ref="tooltipContent" class="styled-tooltip" role="tooltip">
    <slot name="content"></slot>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  name: "StyledTooltip",
  props: {
    placement: {
      type: String,
      default: "bottom-start",
    },
    delay: {
      type: Number,
      default: 500,
    },
    offset: {
      type: Array,
      default: () => [0, 4],
    },
  },
  data() {
    return {
      tooltipTimeout: null,
      popperInstance: null,
    };
  },
  mounted() {
    const anchor = this.$refs.anchor;
    const tooltip = this.$refs.tooltipContent;

    this.popperInstance = createPopper(anchor, tooltip, {
      placement: this.placement,
      strategy: "fixed",
      modifiers: [
        {
          name: "offset",
          options: {
            offset: this.offset,
          },
        },
      ],
    });

    anchor.addEventListener("mouseenter", this.delayedShowTooltip);
    anchor.addEventListener("mouseleave", this.hideTooltip);
    anchor.addEventListener("focus", this.delayedShowTooltip);
    anchor.addEventListener("blur", this.hideTooltip);
  },
  beforeUnmount() {
    const anchor = this.$refs.anchor;
    if (anchor) {
      anchor.removeEventListener("mouseenter", this.delayedShowTooltip);
      anchor.removeEventListener("mouseleave", this.hideTooltip);
      anchor.removeEventListener("focus", this.delayedShowTooltip);
      anchor.removeEventListener("blur", this.hideTooltip);
    }
    if (this.popperInstance) {
      this.popperInstance.destroy();
    }
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        this.$refs.tooltipContent.setAttribute("data-show", "");
        this.popperInstance.update();
      }, this.delay);
    },
    hideTooltip() {
      clearTimeout(this.tooltipTimeout);
      this.$refs.tooltipContent.removeAttribute("data-show");
    },
  },
};
</script>

<style scoped>
.tooltip-anchor {
  display: inline-block;
}

.styled-tooltip {
  z-index: 9999;
  border: 1px solid grey;
  width: auto;
  max-width: 40rem;
  background: #333;
  box-shadow: 0 0 10px cornflowerblue;
  color: white;
  padding: 1em;
  border-radius: 4px;
  white-space: pre-wrap;
  display: none;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.4;
}

.styled-tooltip[data-show] {
  display: block;
}
</style>
