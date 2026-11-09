<template>
  <InputText
    :model-value="modelValue"
    type="text"
    :placeholder="placeholder"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script>
import InputText from "primevue/inputtext";

export default {
  components: { InputText },
  props: {
    modelValue: { type: String, default: null },
    placeholder: { type: String, default: "Search..." },
    options: { type: Array, default: () => [] },
  },
  emits: ["update:modelValue"],
};
</script>
