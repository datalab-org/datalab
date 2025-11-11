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
        @update:model-value="handleUpdateValue"
        @input="handleInput"
      />
    </div>
    <component
      :is="componentName"
      v-else-if="!isVirtualField"
      :id="fieldId"
      v-bind="componentProps"
      @update:model-value="handleUpdateValue"
      @input="handleInput"
    />
    <TableOfContents
      v-else-if="uiConfig.component === 'TableOfContents'"
      :item_id="componentProps.item_id"
      :information-sections="componentProps.informationSections"
    />
    <SynthesisInformation
      v-else-if="uiConfig.component === 'SynthesisInformation'"
      :sample-data="componentProps.sampleData"
      @update-sample-data="$emit('update-nested', $event)"
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
import SynthesisInformation from "@/components/SynthesisInformation";

import { dateTimeParser, dateTimeFormatter } from "@/field_utils.js";

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
    SynthesisInformation,
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
  emits: ["update:modelValue", "input", "update-nested"],
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
        SynthesisInformation,
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
      let value = this.modelValue !== undefined ? this.modelValue : "";

      let inputType = "text";

      const isDatetimeField =
        this.fieldSchema.format === "datetime" ||
        this.fieldSchema.type === "date" ||
        (this.fieldSchema.anyOf &&
          this.fieldSchema.anyOf.some((option) => option.format === "datetime"));

      if (isDatetimeField) {
        inputType = "datetime-local";
        value = dateTimeParser(value);
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
    handleUpdateValue(value) {
      const componentType = this.uiConfig.component || "input";
      if (componentType === "input") {
        const inputType = this.getInputProps().type;
        if (inputType === "datetime-local" && value) {
          value = dateTimeFormatter(value);
        }
      }
      this.$emit("update:modelValue", value);
    },
    handleInput(event) {
      if (event.target && event.target.value !== undefined) {
        const componentType = this.uiConfig.component || "input";
        if (componentType === "input") {
          const inputType = this.getInputProps().type;
          let value = event.target.value;
          if (inputType === "datetime-local" && value) {
            value = dateTimeFormatter(value);
          }
          this.$emit("update:modelValue", value);
        }
      }
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
        SynthesisInformation: {
          sampleData: this.itemData,
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
