<template>
  <div v-if="!isHidden" :class="fieldClass">
    <label v-if="showLabel" :for="fieldId">
      {{ label }}
      <span v-if="isRequired" class="text-danger">*</span>
    </label>

    <component
      :is="componentName"
      :id="fieldId"
      v-bind="componentProps"
      @update:model-value="$emit('update:modelValue', $event)"
      @input="$emit('input', $event)"
    />

    <small v-if="fieldSchema.description && showDescription" class="form-text text-muted">
      {{ fieldSchema.description }}
    </small>
  </div>
</template>

<script>
import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import FormattedRefcode from "@/components/FormattedRefcode";
import FormattedBarcode from "@/components/FormattedBarcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import GHSHazardInformation from "@/components/GHSHazardInformation";

export default {
  name: "DynamicFieldRenderer",
  components: {
    FormattedItemName,
    FormattedCollectionName,
    FormattedRefcode,
    FormattedBarcode,
    Creators,
    ToggleableCollectionFormGroup,
    TinyMceInline,
    ChemFormulaInput,
    GHSHazardInformation,
  },
  props: {
    fieldName: { type: String, required: true },
    fieldSchema: { type: Object, required: true },
    modelValue: { type: [String, Number, Boolean, Array, Object, Date], default: null },
    isRequired: { type: Boolean, default: false },
    showLabel: { type: Boolean, default: true },
    showDescription: { type: Boolean, default: false },
    itemType: { type: String, required: true },
    itemData: { type: Object, required: true },
  },
  emits: ["update:modelValue", "input"],
  computed: {
    uiConfig() {
      return this.fieldSchema.ui || {};
    },
    fieldId() {
      return `${this.itemType}-${this.fieldName}`;
    },
    isHidden() {
      return this.uiConfig.hidden || false;
    },
    isReadonly() {
      return this.uiConfig.readonly || false;
    },
    label() {
      if (this.fieldSchema.title === "Chemform") {
        return "Chemical Formula";
      }
      return this.fieldSchema.title || this.fieldName.replace(/_/g, " ");
    },
    fieldClass() {
      const baseClass = "form-group";
      const width = this.uiConfig.width || "col";
      const needsFlexColumn = this.fieldName === "creators";

      if (needsFlexColumn) {
        return `${baseClass} d-flex flex-column ${width}`;
      }

      return `${baseClass} ${width} pr-2`;
    },
    componentName() {
      const componentMap = {
        FormattedItemName,
        FormattedCollectionName,
        FormattedRefcode,
        FormattedBarcode,
        Creators,
        ToggleableCollectionFormGroup,
        TinyMceInline,
        ChemFormulaInput,
        GHSHazardInformation,
      };

      const componentType = this.uiConfig.component || "input";

      return componentMap[componentType] || "input";
    },
    componentProps() {
      const componentType = this.uiConfig.component || "input";
      const baseProps = {
        modelValue: this.modelValue,
      };

      if (componentType === "input") {
        return this.getInputProps();
      }

      return this.getSpecialComponentProps(componentType, baseProps);
    },
  },
  methods: {
    getInputProps() {
      const value = this.modelValue !== undefined ? this.modelValue : "";

      let inputType = "text";
      if (this.fieldSchema.type === "date" || this.fieldSchema.format === "date-time") {
        inputType = "datetime-local";
      } else if (this.fieldSchema.type === "integer" || this.fieldSchema.type === "number") {
        inputType = "number";
      }

      return {
        value,
        class: "form-control",
        type: inputType,
        disabled: this.isReadonly,
      };
    },
    getSpecialComponentProps(componentType, baseProps) {
      const specialPropsMap = {
        FormattedItemName: {
          ...baseProps,
          itemType: this.itemType,
          item_id: this.itemData.item_id,
          enableClick: true,
        },
        FormattedRefcode: {
          refcode: this.modelValue || "",
          enableQRCode: true,
          enableModifiedClick: true,
        },
        FormattedBarcode: {
          barcode: this.modelValue || "",
        },
        Creators: {
          creators: this.modelValue || [],
          size: "36",
        },
        ToggleableCollectionFormGroup: {
          modelValue: this.itemData[this.fieldName] || [],
        },
        GHSHazardInformation: {
          modelValue: Array.isArray(this.modelValue)
            ? this.modelValue.join(", ")
            : this.modelValue || "",
        },
        ChemFormulaInput: baseProps,
        TinyMceInline: baseProps,
      };

      return specialPropsMap[componentType] || baseProps;
    },
  },
};
</script>
