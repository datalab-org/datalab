<template>
  <input
    :value="modelValue"
    type="datetime-local"
    class="form-control form-control-sm"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script>
export default {
  name: "DatetimeEditor",
  props: {
    modelValue: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
};
</script>
