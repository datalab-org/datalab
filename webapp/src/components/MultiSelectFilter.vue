<template>
  <MultiSelect
    ref="multiselect"
    :model-value="modelValue"
    :options="options"
    :option-label="optionLabel"
    :placeholder="placeholder"
    class="d-flex w-full"
    :filter="true"
    v-bind="$attrs"
    @update:model-value="onValueChange"
    @click.stop
  >
    <template v-if="optionComponent" #option="slotProps">
      <div class="flex items-center">
        <component :is="optionComponent" v-bind="resolveProps(optionProps, slotProps.option)" />
        <span v-if="showOptionLabel && optionLabel" class="ml-1">{{
          slotProps.option[optionLabel]
        }}</span>
      </div>
    </template>
    <template #value="slotProps">
      <div class="flex flex-wrap gap-1 items-center">
        <template v-if="slotProps.value && slotProps.value.length">
          <span
            v-for="(val, index) in slotProps.value"
            :key="index"
            class="inline-flex items-center mr-2"
          >
            <component
              :is="valueComponent || optionComponent"
              v-if="valueComponent || optionComponent"
              v-bind="resolveProps(valueProps || optionProps, val)"
            />
            <template v-else-if="optionLabel">{{ val[optionLabel] }}</template>
            <template v-else>{{ val }}</template>
            <span
              v-if="showOptionLabel && optionLabel && (valueComponent || optionComponent)"
              class="ml-1"
              >{{ val[optionLabel] }}</span
            >
          </span>
        </template>
        <span v-else class="text-gray-400">{{ placeholder }}</span>
      </div>
    </template>
  </MultiSelect>
</template>

<script>
import MultiSelect from "primevue/multiselect";

export default {
  components: { MultiSelect },
  inheritAttrs: false,
  props: {
    modelValue: { type: Array, default: null },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: null },
    placeholder: { type: String, default: "Any" },
    optionComponent: { type: [Object, Function], default: null },
    optionProps: { type: Function, default: null },
    valueComponent: { type: [Object, Function], default: null },
    valueProps: { type: Function, default: null },
    showOptionLabel: { type: Boolean, default: false },
  },
  emits: ["update:modelValue", "apply"],
  methods: {
    onValueChange(value) {
      this.$emit("update:modelValue", value);
      this.$emit("apply");
      this.$nextTick(() => this.$refs.multiselect?.hide?.());
    },
    resolveProps(propsFn, item) {
      if (!propsFn) return {};
      return typeof propsFn === "function" ? propsFn(item) : propsFn;
    },
  },
};
</script>
