<template>
  <StyledTooltip v-if="helpMessage" :delay="500">
    <template #anchor>
      <input
        ref="input"
        v-model="vmodelvalue"
        v-bind="$attrs"
        :readonly="readonly"
        :class="formControlClass"
        :type="type"
      />
    </template>
    <template #content>
      {{ helpMessage }}
    </template>
  </StyledTooltip>
  <input
    v-else
    ref="input"
    v-model="vmodelvalue"
    v-bind="$attrs"
    :readonly="readonly"
    :class="formControlClass"
    :type="type"
  />
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";

// This component is a simple wrapper of <input> that allows for
// proper bootstrap styling when 'readonly' is applied. It also
// allows 'date' inputs to work even if datetime strings are supplied
// (but, the time is discarded!)

export default {
  components: {
    StyledTooltip,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    type: {
      type: String,
      default: "string",
    },
    helpMessage: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
  computed: {
    inputType() {
      if (
        this.modelValue == null &&
        this.readonly &&
        (this.type == "date" || this.type == "datetime-local")
      ) {
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
};
</script>
