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
    <select
      v-else-if="!isVirtualField && componentName === 'select'"
      :id="fieldId"
      :value="componentProps.value"
      :class="componentProps.class"
      :disabled="componentProps.disabled"
      @change="handleSelectChange"
    >
      <option value="">-- Select --</option>
      <option v-for="option in componentProps.options" :key="option" :value="option">
        {{ option }}
      </option>
    </select>
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
    <FieldLabelDescriptionTooltip
      v-if="isVirtualField && fieldSchema.description"
      :html-for="fieldId"
      :label="label"
      :description="fieldSchema.description"
      :icon-only="true"
    />
    <SynthesisInformation
      v-else-if="uiConfig.component === 'SynthesisInformation'"
      :item_id="componentProps.item_id"
    />
    <CellPreparationInformation
      v-else-if="uiConfig.component === 'CellPreparationInformation'"
      :item_id="componentProps.item_id"
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
import CASInput from "@/components/CASInput";
import GHSHazardInformation from "@/components/GHSHazardInformation";
import TableOfContents from "@/components/TableOfContents";
import FieldLabelDescriptionTooltip from "@/components/FieldLabelDescriptionTooltip";
import SynthesisInformation from "@/components/SynthesisInformation";
import CellPreparationInformation from "@/components/CellPreparationInformation";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";

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
    CASInput,
    GHSHazardInformation,
    TableOfContents,
    FieldLabelDescriptionTooltip,
    SynthesisInformation,
    CellPreparationInformation,
    CollectionList,
    Creators,
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
      const virtualFields = [
        "TableOfContents",
        "SynthesisInformation",
        "CellPreparationInformation",
      ];
      const fieldsWithBuiltinLabel = ["CASInput"];
      return (
        this.showLabel &&
        !virtualFields.includes(this.uiConfig.component) &&
        !fieldsWithBuiltinLabel.includes(this.uiConfig.component) &&
        !this.hasBuiltinLabel
      );
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
        CASInput,
        GHSHazardInformation,
        TableOfContents,
        SynthesisInformation,
        CellPreparationInformation,
        CollectionList,
        Creators,
      };

      const componentType = this.uiConfig.component || "input";

      if (componentType === "select") {
        return "select";
      }

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

      if (componentType === "select") {
        return this.getSelectProps();
      }

      return this.getSpecialComponentProps(componentType, baseProps);
    },
    hasBuiltinLabel() {
      return this.uiConfig.has_builtin_label || false;
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
      } else if (
        this.fieldSchema.type === "integer" ||
        this.fieldSchema.type === "number" ||
        (this.fieldSchema.anyOf &&
          this.fieldSchema.anyOf.some(
            (option) => option.type === "number" || option.type === "integer",
          ))
      ) {
        inputType = "number";
      }

      if (this.fieldSchema.enum) {
        return {
          options: this.fieldSchema.enum,
          modelValue: this.modelValue,
          class: "form-control",
        };
      }

      return {
        value,
        class: "form-control",
        type: inputType,
        disabled: this.isReadonly,
      };
    },
    getSelectProps() {
      return {
        value: this.modelValue || "",
        class: "form-control",
        disabled: this.isReadonly,
        options: this.fieldSchema.enum || [],
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
    handleSelectChange(event) {
      this.$emit("update:modelValue", event.target.value);
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
        CollectionList: {
          collections: this.modelValue || [],
        },
        Creators: {
          creators: this.modelValue || [],
          showNames: true,
          size: "36",
        },
        ToggleableCreatorsFormGroup: {
          modelValue: this.modelValue || [],
          size: "36",
          description: this.hasBuiltinLabel ? this.fieldSchema.description : null,
        },
        ToggleableCollectionFormGroup: {
          modelValue: this.itemData[this.fieldName] || [],
          description: this.hasBuiltinLabel ? this.fieldSchema.description : null,
        },
        GHSHazardInformation: {
          modelValue: Array.isArray(this.modelValue)
            ? this.modelValue.join(", ")
            : this.modelValue || "",
          description: this.hasBuiltinLabel ? this.fieldSchema.description : null,
          editable: !this.isReadonly,
        },
        ChemFormulaInput: baseProps,
        CASInput: {
          ...baseProps,
          readonly: this.isReadonly,
          showLabel: true,
          inputId: this.fieldId,
          description: this.hasBuiltinLabel ? this.fieldSchema.description : null,
        },
        TinyMceInline: baseProps,
        TableOfContents: {
          item_id: this.itemData.item_id,
          informationSections: this.getTableOfContentsSections(),
        },
        SynthesisInformation: {
          item_id: this.itemData.item_id,
        },
        CellPreparationInformation: {
          item_id: this.itemData.item_id,
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
