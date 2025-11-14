<template>
  <div class="form-group">
    <FieldLabelDescriptionTooltip
      v-if="showLabel"
      :html-for="inputId"
      label="CAS"
      :description="description"
    >
      <a
        v-if="modelValue"
        :href="casUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="cas-search-link"
        title="Search on Common Chemistry"
      >
        <font-awesome-icon icon="search" class="fixed-width ml-2" />
      </a>
    </FieldLabelDescriptionTooltip>

    <input
      :id="inputId"
      :value="modelValue"
      type="text"
      class="form-control"
      :readonly="readonly"
      :disabled="disabled"
      placeholder="e.g., 7732-18-5"
      @input="handleInput"
    />
  </div>
</template>

<script>
import FieldLabelDescriptionTooltip from "@/components/FieldLabelDescriptionTooltip";

export default {
  name: "CASInput",
  components: { FieldLabelDescriptionTooltip },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    showLabel: {
      type: Boolean,
      default: false,
    },
    inputId: {
      type: String,
      default: "cas-input",
    },
    description: {
      type: String,
      default: null,
    },
  },

  emits: ["update:modelValue"],
  computed: {
    casUrl() {
      return `https://commonchemistry.cas.org/detail?cas_rn=${this.modelValue}`;
    },
  },
  methods: {
    handleInput(event) {
      this.$emit("update:modelValue", event.target.value);
    },
  },
};
</script>

<style scoped>
.cas-label {
  display: flex;
  align-items: center;
}

.cas-search-link {
  color: #007bff;
  text-decoration: none;
  transition: color 0.2s;
}

.cas-search-link:hover {
  color: #0056b3;
}
</style>
