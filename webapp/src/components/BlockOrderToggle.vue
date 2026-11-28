<template>
  <div class="block-order-toggle" data-testid="block-order-toggle">
    <span class="toggle-label">Order blocks by</span>
    <SelectButton
      :model-value="modelValue"
      :options="options"
      option-label="label"
      option-value="value"
      :allow-empty="false"
      size="small"
      aria-label="Block order"
      @update:model-value="select"
    />
  </div>
</template>

<script>
import SelectButton from "primevue/selectbutton";

export const BLOCK_ORDER_MODES = ["manual", "timeline"];
const STORAGE_KEY = "datalab-block-order-mode";

function readStoredMode() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return BLOCK_ORDER_MODES.includes(stored) ? stored : null;
  } catch {
    return null;
  }
}

function storeMode(mode) {
  try {
    window.localStorage.setItem(STORAGE_KEY, mode);
    return true;
  } catch {
    return false;
  }
}

export default {
  components: { SelectButton },
  props: {
    modelValue: {
      type: String,
      default: "manual",
      validator: (value) => BLOCK_ORDER_MODES.includes(value),
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      options: [
        { label: "Manual", value: "manual" },
        { label: "Timeline", value: "timeline" },
      ],
    };
  },
  mounted() {
    const stored = readStoredMode();
    if (stored && stored !== this.modelValue) {
      this.$emit("update:modelValue", stored);
    }
  },
  methods: {
    select(mode) {
      if (!BLOCK_ORDER_MODES.includes(mode)) {
        return;
      }
      storeMode(mode);
      this.$emit("update:modelValue", mode);
    },
  },
};
</script>

<style scoped>
.block-order-toggle {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.toggle-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}
</style>
