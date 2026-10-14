<template>
  <!-- TODO: replace with ChemFormulaInput when backend schema defines chemical-formula editor -->
  <input
    :value="modelValue"
    type="text"
    class="form-control form-control-sm"
    placeholder="e.g. LiFePO4"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script>
export default {
  name: "ChemicalFormulaEditor",
  props: {
    modelValue: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
};
</script>
