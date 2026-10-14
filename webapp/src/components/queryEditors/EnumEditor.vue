<template>
  <select
    :value="modelValue || ''"
    class="custom-select custom-select-sm"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option value="" disabled>Select…</option>
    <option v-for="opt in options" :key="opt" :value="opt">{{ opt }}</option>
  </select>
</template>

<script>
export default {
  name: "EnumEditor",
  props: {
    modelValue: { type: String, default: null },
    valueSchema: { type: Object, default: () => ({}) },
  },
  emits: ["update:modelValue"],
  computed: {
    options() {
      return this.valueSchema?.enum || [];
    },
  },
};
</script>
