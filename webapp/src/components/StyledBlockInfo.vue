<template>
  <a
    ref="anchor"
    @mouseenter="delayedShowTooltip"
    @mouseleave="hideTooltip"
    @focus="delayedShowTooltip"
    @blur="hideTooltip"
  >
    <font-awesome-icon :icon="['fas', 'info-circle']" @click="showBlockInfo" />
  </a>
  <div ref="tooltipContent" id="tooltip" role="tooltip">
    <h4 class="block-info-title">{{ blockInfo.attributes.name }}</h4>
    <p>{{ blockInfo.attributes.description }}</p>
    <div
      v-if="
        blockInfo.attributes.accepted_file_extensions != null &&
        blockInfo.attributes.accepted_file_extensions.length > 0
      "
    >
      Accepted file extensions:
      <ul>
        <span
          v-for="(extension, index) in blockInfo.attributes.accepted_file_extensions"
          :key="index"
        >
          <li class="filetype-li">{{ extension }}</li>
        </span>
      </ul>
    </div>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  name: "StyledBlockInfo",
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
      }, 100);
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
  width: 25%;
  background: #333;
  box-shadow: 0 0 10px cornflowerblue;
  color: white;
  font-weight: bold;
  padding: 1em;
  border-radius: 4px;
}

.block-info-title {
  /* add wavy blue underline */
  text-decoration: underline;
  text-decoration-color: cornflowerblue;
  text-decoration-style: wavy;
}

.filetype-li {
  font-family: "Roboto Mono", monospace;
}

#tooltip {
  display: none;
}

#tooltip[data-show] {
  display: block;
}
</style>
