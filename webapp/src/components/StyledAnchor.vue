<template>
  <a
    ref="anchor"
    class="dropdown-item"
    @mouseenter="delayedShowTooltip"
    @mouseleave="hideTooltip"
    @focus="delayedShowTooltip"
    @blur="hideTooltip"
    >{{ blockInfo.name }}</a
  >
  <div ref="tooltipContent" id="tooltip" role="tooltip">
    <p class="tooltipTitle">{{ blockInfo.name }}</p>
    <p>{{ blockInfo.description }}</p>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  name: "StyledAnchor",
  props: {
    blockInfo: {
      type: Object,
    },
  },
  data() {
    return {
      tooltipDisplay: false,
      tooltipTimeout: null,
      popperInstance: null,
    };
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        if (this.blockInfo) {
          this.$refs.tooltipContent.setAttribute("data-show", "");
          this.popperInstance.update();
        }
      }, 1000);
    },

    hideTooltip() {
      clearTimeout(this.tooltipTimeout);
      this.$refs.tooltipContent.removeAttribute("data-show");
    },
  },
  mounted() {
    const anchor = this.$refs.anchor;
    const tooltip = this.$refs.tooltipContent;

    this.popperInstance = createPopper(anchor, tooltip, {
      placement: "bottom-start",
      strategy: "fixed",
      modifiers: [
        {
          name: "offset",
          options: {
            offset: [0, 4],
          },
        },
      ],
    });
  },
};
</script>

<style scoped>
input {
  border: 1px solid grey;
}

#tooltip {
  z-index: 9999;
  border: 1px solid grey;
  width: auto;
  background: #333;
  color: white;
  font-weight: bold;
  padding: 1em;
  border-radius: 4px;
}

#tooltip {
  display: none;
}

#tooltip[data-show] {
  display: block;
}
</style>
