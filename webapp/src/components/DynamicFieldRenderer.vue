<template>
  <div v-if="!isHidden" :class="fieldClass">
    <FieldLabelDescriptionTooltip
      v-if="shouldShowLabel"
      :html-for="fieldId"
      :label="label"
      :description="fieldSchema.description"
    >
      <span v-if="isRequired" class="text-danger">*</span>
    </FieldLabelDescriptionTooltip>

    <div v-if="needsWrapper" :id="fieldId">
      <component
        :is="componentName"
        v-bind="componentProps"
        @update:model-value="$emit('update:modelValue', $event)"
        @input="$emit('input', $event)"
      />
    </div>
    <component
      :is="componentName"
      v-else-if="!isVirtualField"
      :id="fieldId"
      v-bind="componentProps"
      @update:model-value="$emit('update:modelValue', $event)"
      @input="$emit('input', $event)"
    />
    <TableOfContents
      v-else-if="uiConfig.component === 'TableOfContents'"
      :item_id="componentProps.item_id"
      :information-sections="componentProps.informationSections"
    />
  </div>
</template>

<script>
import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import FormattedRefcode from "@/components/FormattedRefcode";
import FormattedBarcode from "@/components/FormattedBarcode";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import GHSHazardInformation from "@/components/GHSHazardInformation";
import TableOfContents from "@/components/TableOfContents";
import FieldLabelDescriptionTooltip from "@/components/FieldLabelDescriptionTooltip";

export default {
  name: "DynamicFieldRenderer",
  components: {
    FormattedItemName,
    FormattedCollectionName,
    FormattedRefcode,
    FormattedBarcode,
    ToggleableCreatorsFormGroup,
    ToggleableCollectionFormGroup,
    TinyMceInline,
    ChemFormulaInput,
    GHSHazardInformation,
    TableOfContents,
    FieldLabelDescriptionTooltip,
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
    isVirtualField() {
      return this.fieldSchema.type === "null";
    },

    shouldShowLabel() {
      if (this.uiConfig.hide_label) {
        return false;
      }
      return this.showLabel;
    },
    needsWrapper() {
      const wrapperComponents = ["FormattedRefcode", "FormattedBarcode"];
      return wrapperComponents.includes(this.uiConfig.component);
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

      return `${baseClass} ${width}`;
    },
    componentName() {
      const componentMap = {
        FormattedItemName,
        FormattedCollectionName,
        FormattedRefcode,
        FormattedBarcode,
        ToggleableCreatorsFormGroup,
        ToggleableCollectionFormGroup,
        TinyMceInline,
        ChemFormulaInput,
        GHSHazardInformation,
        TableOfContents,
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
        ToggleableCreatorsFormGroup: {
          modelValue: this.modelValue || [],
          refcode: this.itemData.refcode,
        },
        ToggleableCollectionFormGroup: {
          modelValue: this.itemData[this.fieldName] || [],
          item_id: this.itemData.item_id,
        },
        GHSHazardInformation: {
          modelValue: Array.isArray(this.modelValue)
            ? this.modelValue.join(", ")
            : this.modelValue || "",
        },
        ChemFormulaInput: baseProps,
        TinyMceInline: baseProps,
        TableOfContents: {
          item_id: this.itemData.item_id,
          informationSections: this.getTableOfContentsSections(),
        },
      };

      return specialPropsMap[componentType] || baseProps;
    },
    getTableOfContentsSections() {
      const sections = [
        {
          title: `${this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)} Information`,
          targetID: `${this.itemType}-information`,
        },
      ];

      if (this.itemType === "samples" && this.itemData.synthesis_constituents) {
        sections.push({
          title: "Synthesis Information",
          targetID: "synthesis-information",
        });
      }

      if (this.itemType === "cells" && this.itemData.characteristic_mass) {
        sections.push({
          title: "Cell Preparation Information",
          targetID: "cell-preparation-information",
        });
      }

      return sections;
    },
  },
};
</script>
