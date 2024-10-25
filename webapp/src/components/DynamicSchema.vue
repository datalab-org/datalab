<template>
  <div v-if="schema?.properties" class="container-lg">
    <div class="row">
      <div class="col">
        <div class="form-row">
          <div v-for="(field, index) in displayedSchemaFields" :key="index" class="col-md-4">
            <label v-if="field != 'relationships' && field != 'collections'" :for="field">{{
              schema.properties[field].title
            }}</label>

            <component
              :is="getComponentType(field)"
              :key="index"
              :placeholder="field.title"
              v-bind="getComponentProps(field)"
              @update:model-value="handleModelValueUpdate(field, $event)"
              @input="handleInput(field, $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSchema } from "@/server_fetch_utils";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";

export default {
  props: {
    item_data: { type: Object, required: true },
  },
  emits: ["update-item-data"],
  data() {
    return {
      schema: null,
      localItemData: { ...this.item_data },
      displayedFields: [],
    };
  },
  computed: {
    displayedSchemaFields() {
      return this.displayedFields.length > 0
        ? Object.keys(this.schema.properties).filter((field) =>
            this.displayedFields.includes(field),
          )
        : Object.keys(this.schema.properties);
    },
  },
  watch: {
    item_data: {
      handler(newVal) {
        this.localItemData = { ...newVal };
      },
      deep: true,
    },
  },
  async mounted() {
    this.schema = await getSchema(this.item_data.type);
    this.setDisplayedFields(this.item_data.type);
  },

  methods: {
    handleInput(field, event) {
      const value = event?.target?.value;
      if (value !== undefined) {
        this.updateField(field, value);
      }
    },
    updateField(field, value) {
      this.localItemData = {
        ...this.localItemData,
        [field]: value,
      };

      this.$emit("update-item-data", {
        item_id: this.item_data.item_id,
        item_data: this.localItemData,
      });
    },
    setDisplayedFields(schemaType) {
      const defaultFields = ["name", "date", "refcode", "creators", "collections", "description"];
      switch (schemaType) {
        case "samples":
          this.displayedFields = [...defaultFields, "chemform", "relationships"];
          break;
        case "cells":
          this.displayedFields = [
            ...defaultFields,
            "relationships",
            "cell_format",
            "cell_format_description",
            "characteristic_mass",
            "characteristic_chemical_formula",
            "characteristic_molar_mass",
          ];
          break;
        case "equipments":
          this.displayedFields = [
            ...defaultFields,
            "manufacturer",
            "location",
            "serial_numbers",
            "contact",
          ];
          break;
        case "starting_materials":
          this.displayedFields = [
            ...defaultFields,
            "CAS",
            "GHS_codes",
            "date_opened",
            "chemform",
            "supplier",
            "chemical_purity",
            "location",
          ];
          break;
      }
    },
    getComponentType(field) {
      switch (field) {
        case "item_id":
          return FormattedItemName;
        case "collection_id":
          return FormattedCollectionName;
        case "refcode":
          return FormattedRefcode;
        case "creators":
          return Creators;
        case "collections":
          return ToggleableCollectionFormGroup;
        case "description":
          return TinyMceInline;
        case "relationships":
          return ItemRelationshipVisualization;
        default:
          return "input";
      }
    },

    getComponentProps(field) {
      const fieldSchema = this.schema.properties[field];
      const componentType = this.getComponentType(field);
      const baseProps = {
        modelValue: this.localItemData[field],
        "onUpdate:modelValue": (value) => this.handleModelValueUpdate(field, value),
      };

      if (componentType === "input") {
        return {
          value: this.localItemData[field] !== undefined ? this.localItemData[field] : "",
          class: "form-control",
          ...(fieldSchema.type === "date" && { type: "datetime-local" }),
          ...(fieldSchema.type === "string" && { type: "text" }),
          ...(fieldSchema.type === "integer" && { type: "number" }),
          ...(fieldSchema.type === "array" && { class: "form-control" }),
          ...(fieldSchema.type === "object" && { class: "form-control" }),
        };
      }

      switch (field) {
        case "item_id":
          return {
            ...baseProps,
            itemType: this.localItemData.type,
            item_id: this.localItemData.item_id,
            enableClick: true,
          };
        case "description":
        case "collections":
          return baseProps;
        case "relationships":
          return {
            ...baseProps,
            item_id: this.localItemData.item_id,
          };
        default:
          return {
            ...baseProps,
            [field]: this.localItemData[field],
          };
      }
    },
  },
};
</script>
