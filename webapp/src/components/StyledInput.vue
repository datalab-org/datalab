<template>
  <input
    :type="inputType"
    :class="{ 'form-control': !readonly, 'form-control-plaintext': readonly }"
    :readonly="readonly"
    v-model="vmodelvalue"
  />
</template>

<script>
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
  },
  computed: {
    inputType() {
      if (this.readonly && (this.type == "date" || this.type == "datetime-local")) {
        return "text";
      }
      return this.type;
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
