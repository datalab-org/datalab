<template>
  <input
    :value="modelValue"
    type="text"
    class="form-control form-control-sm"
    placeholder="Enter value…"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script>
export default {
  name: "TextEditor",
  props: { modelValue: { type: String, default: "" } },
  emits: ["update:modelValue"],
};
</script>
