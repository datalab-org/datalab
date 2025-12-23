<template>
  <vSelect ref="selectComponent" v-model="value" :options="options">
    <template #option="option">
      <FormattedItemStatus :dot-only="false" :status="option.label" />
    </template>
    <template #selected-option="option">
      <FormattedItemStatus :dot-only="false" :status="option.label" />
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import FormattedItemStatus from "@/components/FormattedItemStatus.vue";

export default {
  components: {
    vSelect,
    FormattedItemStatus,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
    options: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  computed: {
    // computed setter to pass v-model through  component:
    value: {
      get() {
        return this.modelValue;
      },
      set(newValue) {
        this.$emit("update:modelValue", newValue);
      },
    },
  },
};
</script>
