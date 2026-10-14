<template>
  <div>
    <textarea
      :value="displayValue"
      class="form-control form-control-sm"
      rows="2"
      placeholder="JSON value"
      @input="onInput($event.target.value)"
    />
    <small v-if="parseError" class="text-danger">{{ parseError }}</small>
  </div>
</template>

<script>
export default {
  name: "FallbackEditor",
  props: {
    modelValue: { type: [String, Number, Array, Object], default: null },
    valueSchema: { type: Object, default: null },
  },
  emits: ["update:modelValue"],
  data() {
    return { parseError: null };
  },
  computed: {
    displayValue() {
      if (this.modelValue === null || this.modelValue === undefined) return "";
      if (typeof this.modelValue === "string") return this.modelValue;
      return JSON.stringify(this.modelValue, null, 2);
    },
  },
  methods: {
    onInput(raw) {
      this.parseError = null;
      try {
        const parsed = JSON.parse(raw);
        this.$emit("update:modelValue", parsed);
      } catch {
        this.parseError = "Invalid JSON";
        this.$emit("update:modelValue", raw);
      }
    },
  },
};
</script>
