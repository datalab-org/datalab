<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="options"
    :reduce="(folder) => folder"
    placeholder="Select a folder"
    v-bind="$attrs"
    class="folder-select"
  >
    <template #option="{ label }">
      <span class="folder-name">./{{ label }}</span>
    </template>
    <template #selected-option="{ label }">
      <span class="folder-name">./{{ label }}</span>
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
      type: [String, Array],
      default: "",
    },
    options: {
      type: Array,
      default: () => [],
    },
    reduce: {
      type: Function,
      default: (option) => option,
    },
    placeholder: {
      type: String,
      default: "",
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

<style scoped>
.folder-select {
  width: 100%;
}

.folder-name {
  font-family: monospace;
}
</style>
