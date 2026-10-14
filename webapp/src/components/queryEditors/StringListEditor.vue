<template>
  <input
    :value="text"
    type="text"
    class="form-control form-control-sm"
    placeholder="val1, val2, ..."
    @input="onInput($event.target.value)"
  />
</template>

<script>
const parse = (raw) =>
  raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

export default {
  name: "StringListEditor",
  props: {
    modelValue: { type: Array, default: () => [] },
  },
  emits: ["update:modelValue"],
  data() {
    // The text is kept as typed: re-deriving it from the parsed list would drop a
    // trailing comma, making it impossible to type a second value.
    return { text: (this.modelValue || []).join(", ") };
  },
  watch: {
    modelValue(next) {
      const current = parse(this.text);
      const values = next || [];
      if (values.length !== current.length || values.some((v, i) => v !== current[i])) {
        this.text = values.join(", ");
      }
    },
  },
  methods: {
    onInput(raw) {
      this.text = raw;
      this.$emit("update:modelValue", parse(raw));
    },
  },
};
</script>
