<template>
  <vSelect ref="selectComponent" v-model="value" :options="options">
    <template #option="option">
      <span :class="'badge-info'" class="badge badge-pill text-uppercase text-monospace">{{
        option.label
      }}</span>
    </template>
    <template #selected-option="option">
      <span :class="'badge-info'" class="badge badge-pill text-uppercase text-monospace">{{
        option.label
      }}</span>
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";

export default {
  components: {
    vSelect,
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
