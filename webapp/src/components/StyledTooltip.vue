<template>
  <div ref="anchor" class="tooltip-anchor" :class="anchorClass">
    <slot name="anchor"></slot>
  </div>
  <Teleport to="body">
    <div ref="tooltipContent" class="styled-tooltip" role="tooltip" data-testid="styled-tooltip">
      <slot name="content"></slot>
    </div>
  </Teleport>
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
    anchorDisplay: {
      type: String,
      default: "inline-block",
    },
    anchorClass: {
      type: String,
      default: "",
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
    anchor.addEventListener("focusin", this.delayedShowTooltip);
    anchor.addEventListener("focusout", this.hideTooltip);

    document.addEventListener("mousedown", this.handleClickOutside);
    window.addEventListener("scroll", this.hideTooltip, true);
  },
  beforeUnmount() {
    const anchor = this.$refs.anchor;
    if (anchor) {
      anchor.removeEventListener("mouseenter", this.delayedShowTooltip);
      anchor.removeEventListener("mouseleave", this.hideTooltip);
      anchor.removeEventListener("focusin", this.delayedShowTooltip);
      anchor.removeEventListener("focusout", this.hideTooltip);
    }
    if (this.popperInstance) {
      this.popperInstance.destroy();
    }

    document.removeEventListener("mousedown", this.handleClickOutside);
    window.removeEventListener("scroll", this.hideTooltip, true);
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        if (this.$refs.tooltipContent && this.popperInstance) {
          this.$refs.tooltipContent.setAttribute("data-show", "");
          this.popperInstance.update();
        }
      }, this.delay);
    },
    hideTooltip() {
      clearTimeout(this.tooltipTimeout);
      if (this.$refs.tooltipContent) {
        this.$refs.tooltipContent.removeAttribute("data-show");
      }
    },
    handleClickOutside(event) {
      const anchor = this.$refs.anchor;
      const tooltip = this.$refs.tooltipContent;

      if (!anchor || !tooltip) return;

      if (!anchor.contains(event.target) && !tooltip.contains(event.target)) {
        this.hideTooltip();
      }
    },
  },
};
</script>

<style scoped>
.tooltip-anchor {
  display: v-bind(anchorDisplay);
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

.styled-tooltip :deep(h4.tooltip-title),
.styled-tooltip :deep(.tooltip-title) {
  text-decoration: underline;
  text-decoration-color: cornflowerblue;
  text-decoration-style: wavy;
  margin-top: 0;
  margin-bottom: 0.5em;
  font-size: 2em;
  font-weight: 500;
}

.styled-tooltip :deep(p) {
  margin: 0;
  margin-bottom: 0.5em;
}

.styled-tooltip :deep(p:last-child) {
  margin-bottom: 0;
}

.styled-tooltip :deep(.accepted-file) {
  padding-top: 0.5em;
}

.styled-tooltip :deep(.filetype-li) {
  font-family: var(--font-monospace);
}
</style>
