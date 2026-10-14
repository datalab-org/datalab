<template>
  <div class="form-row align-items-center">
    <div class="col">
      <!-- TODO: Render structured subfields hierarchically; flat dot-path fields work for now. -->
      <select
        :value="node.field"
        class="custom-select custom-select-sm"
        aria-label="Field"
        @change="onFieldChange($event.target.value)"
      >
        <option value="" disabled>Field…</option>
        <optgroup v-for="group in groupedFields" :key="group.label" :label="group.label">
          <option v-for="f in group.fields" :key="f.id" :value="f.id">{{ f.label }}</option>
        </optgroup>
      </select>
    </div>

    <div class="col">
      <select
        :value="node.operator"
        class="custom-select custom-select-sm"
        aria-label="Operator"
        :disabled="!node.field"
        @change="onOperatorChange($event.target.value)"
      >
        <option value="" disabled>Operator…</option>
        <option v-for="op in availableOperators" :key="op.id" :value="op.id">{{ op.label }}</option>
      </select>
    </div>

    <div class="col">
      <component
        :is="editorComponent"
        v-if="currentOperator && currentOperator.value_required"
        :model-value="node.value"
        :value-schema="currentOperator.value_schema"
        @update:model-value="onValueChange"
      />
      <small v-else-if="currentOperator" class="text-muted font-italic">no value needed</small>
    </div>

    <div class="col-auto">
      <button
        type="button"
        class="btn btn-sm btn-link text-danger"
        title="Remove"
        aria-label="Remove"
        @click="$emit('remove')"
      >
        <font-awesome-icon icon="trash" />
      </button>
    </div>
  </div>
</template>

<script>
import TextEditor from "@/components/queryEditors/TextEditor.vue";
import StringListEditor from "@/components/queryEditors/StringListEditor.vue";
import NumberEditor from "@/components/queryEditors/NumberEditor.vue";
import DatetimeEditor from "@/components/queryEditors/DatetimeEditor.vue";
import EnumEditor from "@/components/queryEditors/EnumEditor.vue";
import ChemicalFormulaEditor from "@/components/queryEditors/ChemicalFormulaEditor.vue";
import ConstituentSelectorEditor from "@/components/queryEditors/ConstituentSelectorEditor.vue";
import FallbackEditor from "@/components/queryEditors/FallbackEditor.vue";

const editorMap = {
  text: "TextEditor",
  "string-list": "StringListEditor",
  number: "NumberEditor",
  datetime: "DatetimeEditor",
  enum: "EnumEditor",
  "chemical-formula": "ChemicalFormulaEditor",
  "constituent-selector": "ConstituentSelectorEditor",
};

export default {
  name: "QueryRule",
  components: {
    TextEditor,
    StringListEditor,
    NumberEditor,
    DatetimeEditor,
    EnumEditor,
    ChemicalFormulaEditor,
    ConstituentSelectorEditor,
    FallbackEditor,
  },
  props: {
    node: { type: Object, required: true },
    fields: { type: Array, required: true },
  },
  emits: ["update:node", "remove"],
  computed: {
    groupedFields() {
      const groups = {};
      this.fields.forEach((f) => {
        const g = f.group || "Other";
        if (!groups[g]) groups[g] = { label: g, fields: [] };
        groups[g].fields.push(f);
      });
      return Object.values(groups);
    },
    currentField() {
      return this.fields.find((f) => f.id === this.node.field) || null;
    },
    availableOperators() {
      return this.currentField ? this.currentField.operators : [];
    },
    currentOperator() {
      if (!this.currentField) return null;
      return this.currentField.operators.find((op) => op.id === this.node.operator) || null;
    },
    editorComponent() {
      if (!this.currentOperator) return null;
      return editorMap[this.currentOperator.editor] || "FallbackEditor";
    },
  },
  methods: {
    onFieldChange(fieldId) {
      const field = this.fields.find((f) => f.id === fieldId);
      const firstOp = field?.operators[0]?.id || "";
      this.$emit("update:node", {
        ...this.node,
        field: fieldId,
        operator: firstOp,
        value: undefined,
      });
    },
    onOperatorChange(opId) {
      this.$emit("update:node", { ...this.node, operator: opId, value: undefined });
    },
    onValueChange(value) {
      this.$emit("update:node", { ...this.node, value });
    },
  },
};
</script>
