<template>
  <vSelect ref="selectComponent" v-model="value" :options="options">
    <template #option="option">
      <FormattedItemAvailability :dot-only="false" :availability="option.label" />
    </template>
    <template #selected-option="option">
      <FormattedItemAvailability :dot-only="false" :availability="option.label" />
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import FormattedItemAvailability from "@/components/FormattedItemAvailability.vue";

export default {
  components: {
    vSelect,
    FormattedItemAvailability,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    options: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue"],
  computed: {
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
