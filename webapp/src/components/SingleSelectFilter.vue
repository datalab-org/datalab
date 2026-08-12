<template>
  <Select
    :model-value="modelValue"
    :options="options"
    :option-label="optionLabel"
    :option-value="optionValue"
    :placeholder="placeholder"
    :show-clear="showClear"
    class="p-column-filter"
    v-bind="$attrs"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template v-if="optionComponent" #option="slotProps">
      <component :is="optionComponent" v-bind="resolveProps(optionProps, slotProps.option)" />
    </template>
    <template v-if="optionComponent || valueComponent" #value="slotProps">
      <component
        :is="valueComponent || optionComponent"
        v-if="slotProps.value !== null && slotProps.value !== undefined"
        v-bind="resolveProps(valueProps || optionProps, slotProps.value)"
      />
      <span v-else>{{ placeholder }}</span>
    </template>
  </Select>
</template>

<script>
import Select from "primevue/select";

export default {
  components: { Select },
  inheritAttrs: false,
  props: {
    modelValue: { type: [String, Boolean, Object], default: null },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: null },
    optionValue: { type: String, default: null },
    placeholder: { type: String, default: "Any" },
    showClear: { type: Boolean, default: false },
    optionComponent: { type: [Object, Function], default: null },
    optionProps: { type: Function, default: null },
    valueComponent: { type: [Object, Function], default: null },
    valueProps: { type: Function, default: null },
  },
  emits: ["update:modelValue"],
  methods: {
    resolveProps(propsFn, item) {
      if (!propsFn) return {};
      return typeof propsFn === "function" ? propsFn(item) : propsFn;
    },
  },
};
</script>
