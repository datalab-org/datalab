<template>
  <input
    :value="modelValue"
    type="number"
    class="form-control form-control-sm"
    placeholder="Enter number…"
    @input="onInput($event.target.value)"
  />
</template>

<script>
export default {
  name: "NumberEditor",
  props: { modelValue: { type: Number, default: null } },
  emits: ["update:modelValue"],
  methods: {
    onInput(raw) {
      this.$emit("update:modelValue", raw === "" ? null : Number(raw));
    },
  },
};
</script>
