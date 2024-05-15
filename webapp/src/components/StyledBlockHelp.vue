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
    <p>{{ blockInfo.description }}</p>
    <p
      class="accepted-file"
      v-if="
        blockInfo.accepted_file_extensions != null && blockInfo.accepted_file_extensions.length > 0
      "
    >
      Accepted file extensions:
      <span v-for="(extension, index) in blockInfo.accepted_file_extensions" :key="index">
        {{ extension }}{{ index < blockInfo.accepted_file_extensions.length - 1 ? ", " : "" }}
      </span>
    </p>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  name: "StyledBlockHelp",
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
      }, 500);
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

#tooltip p {
  margin: 0;
}

.accepted-file {
  padding-top: 0.5em;
}

#tooltip {
  display: none;
}

#tooltip[data-show] {
  display: block;
}
</style>
