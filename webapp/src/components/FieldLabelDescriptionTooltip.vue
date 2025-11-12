<template>
  <div
    ref="labelContainer"
    class="field-label-container"
    @mouseenter="delayedShowTooltip"
    @mouseleave="hideTooltip"
  >
    <label v-if="!iconOnly" :for="htmlFor" class="label-text">
      {{ label }}
      <slot></slot>
      <span
        v-if="description"
        ref="anchor"
        tabindex="0"
        class="info-icon"
        @focus="delayedShowTooltip"
        @blur="hideTooltip"
      >
        <font-awesome-icon :icon="['fas', 'info-circle']" />
      </span>
    </label>
    <span
      v-else-if="description"
      ref="anchor"
      tabindex="0"
      class="info-icon"
      @focus="delayedShowTooltip"
      @blur="hideTooltip"
    >
      <font-awesome-icon :icon="['fas', 'info-circle']" />
    </span>
    <div v-if="description" ref="tooltipContent" class="field-tooltip" role="tooltip">
      {{ description }}
    </div>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  name: "FieldLabelWithTooltip",
  props: {
    htmlFor: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      default: null,
    },
    iconOnly: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      tooltipTimeout: null,
      popperInstance: null,
    };
  },
  mounted() {
    if (this.description) {
      const anchor = this.$refs.anchor;
      const tooltip = this.$refs.tooltipContent;

      this.popperInstance = createPopper(anchor, tooltip, {
        placement: "right",
        strategy: "fixed",
        modifiers: [
          {
            name: "offset",
            options: {
              offset: [0, 8],
            },
          },
        ],
      });
    }
  },
  beforeUnmount() {
    if (this.popperInstance) {
      this.popperInstance.destroy();
    }
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        if (this.description && this.$refs.tooltipContent) {
          this.$refs.tooltipContent.setAttribute("data-show", "");
          this.popperInstance.update();
        }
      }, 300);
    },
    hideTooltip() {
      clearTimeout(this.tooltipTimeout);
      if (this.$refs.tooltipContent) {
        this.$refs.tooltipContent.removeAttribute("data-show");
      }
    },
  },
};
</script>

<style scoped>
.field-label-container {
  margin-bottom: 0.5rem;
}

.label-text {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.info-icon {
  font-size: 0.875rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.label-text:hover .info-icon,
.info-icon:focus {
  opacity: 1;
  outline: none;
}

.field-tooltip {
  z-index: 9999;
  border: 1px solid #dee2e6;
  background: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  color: white;
  padding: 0.75rem;
  border-radius: 4px;
  max-width: 20rem;
  font-size: 0.875rem;
  font-weight: normal;
  line-height: 1.4;
  display: none;
}

.field-tooltip[data-show] {
  display: block;
}
</style>
