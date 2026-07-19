<template>
  <div style="display: flex; flex-direction: column; gap: 0.5rem" @click.stop>
    <Select
      v-model="mode"
      :options="modeOptions"
      option-label="label"
      option-value="value"
      placeholder="Select filter type"
      class="w-full"
      @change="onModeChange"
    />
    <DatePicker
      v-if="mode === 'range'"
      :model-value="modelValue"
      selection-mode="range"
      date-format="yy-mm-dd"
      placeholder="Select date range"
      :show-button-bar="true"
      :manual-input="false"
      :hide-on-range-selection="true"
      style="width: 100%"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <DatePicker
      v-else
      :model-value="modelValue"
      date-format="yy-mm-dd"
      :placeholder="mode === 'before' ? 'Before date' : 'After date'"
      :show-button-bar="true"
      :manual-input="false"
      style="width: 100%"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script>
import Select from "primevue/select";
import DatePicker from "primevue/datepicker";

export default {
  components: { Select, DatePicker },
  props: {
    modelValue: { type: [Date, Array], default: null },
    options: { type: Array, default: () => [] },
    currentMatchMode: { type: String, default: null },
  },
  emits: ["update:modelValue", "update:matchMode"],
  data() {
    return {
      mode: "range",
      modeOptions: [
        { label: "Date range", value: "range" },
        { label: "Created before", value: "before" },
        { label: "Created after", value: "after" },
      ],
    };
  },
  created() {
    const modeMap = { dateRange: "range", dateBefore: "before", dateAfter: "after" };
    if (this.currentMatchMode) this.mode = modeMap[this.currentMatchMode] || "range";
  },
  methods: {
    onModeChange() {
      this.$emit("update:modelValue", null);
      const matchModeMap = { range: "dateRange", before: "dateBefore", after: "dateAfter" };
      this.$emit("update:matchMode", matchModeMap[this.mode]);
    },
  },
};
</script>
