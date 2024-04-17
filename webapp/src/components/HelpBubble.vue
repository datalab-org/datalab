<template>
  <div class="help-bubble">
    <Tooltip ref="tooltip">
      <span
        tabindex="0"
        id="icon"
        aria-describedby="tooltip"
        @mouseenter="showTooltip"
        @mouseleave="hideTooltip"
        @focus="showTooltip"
        @blur="hideTooltip"
      >
        <font-awesome-icon icon="info-circle" />
      </span>

      <div ref="tooltipContent" id="tooltip" role="tooltip">
        {{ message }}
      </div>
    </Tooltip>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  props: {
    message: {
      type: String,
      required: true,
    },
  },
  methods: {
    showTooltip() {
      this.$refs.tooltipContent.setAttribute("data-show", "");
      this.popperInstance.update();
    },
    hideTooltip() {
      this.$refs.tooltipContent.removeAttribute("data-show");
    },
  },
  mounted() {
    const button = this.$refs.button;
    const tooltip = this.$refs.tooltipContent;

    this.popperInstance = createPopper(button, tooltip, {
      modifiers: [
        {
          name: "offset",
          options: {
            offset: [0, 8],
          },
        },
      ],
    });
  },
};
</script>

<style scoped>
.help-bubble {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 0.5em;
}

#tooltip {
  position: absolute;
  z-index: 9999;
  border: 1px solid grey;
  background: #333;
  color: white;
  font-weight: bold;
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
}

#tooltip {
  display: none;
}

#tooltip[data-show] {
  display: block;
}
</style>
