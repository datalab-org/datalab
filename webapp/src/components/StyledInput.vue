<template>
  <input
    ref="input"
    :type="inputType"
    :class="formControlClass"
    :readonly="readonly"
    v-model="vmodelvalue"
    @mouseenter="delayedShowTooltip"
    @mouseleave="hideTooltip"
    @focus="delayedShowTooltip"
    @blur="hideTooltip"
    v-bind="$attrs"
  />
  <div ref="tooltipContent" id="tooltip" role="tooltip">
    {{ helpMessage }}
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

// This component is a simple wrapper of <input> that allows for
// proper bootstrap styling when 'readonly' is applied. It also
// allows 'date' inputs to work even if datetime strings are supplied
// (but, the time is discarded!)

export default {
  props: {
    modelValue: { default: "" },
    readonly: {
      type: Boolean,
      default: false,
    },
    type: { default: "string" },
    helpMessage: { type: String },
  },
  data() {
    return {
      tooltipDisplay: false,
      tooltipTimeout: null,
      popperInstance: null,
    };
  },
  computed: {
    inputType() {
      if (this.readonly && (this.type == "date" || this.type == "datetime-local")) {
        return "text";
      }
      return this.type;
    },
    formControlClass() {
      // If the component $attrs specify "form-control" or "form-control-plaintext",
      // don't set any class. Otherwise, set the appropriate class based on whether
      // readonly is specified
      const classes = this.$attrs.class ? this.$attrs.class.split(" ") : [];
      if (classes.includes("form-control") || classes.includes("form-control-plaintext")) {
        return "";
      }
      return this.readonly ? "form-control-plaintext" : "form-control";
    },
    vmodelvalue: {
      get() {
        if (this.type == "date") {
          return this.modelValue && this.modelValue.split("T")[0];
        }
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        if (this.helpMessage) {
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
    const input = this.$refs.input;
    const tooltip = this.$refs.tooltipContent;

    console.log(input);

    this.popperInstance = createPopper(input, tooltip, {
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
#tooltip {
  z-index: 9999;
  border: 1px solid grey;
  width: 30%;
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
