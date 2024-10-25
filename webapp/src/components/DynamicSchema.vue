<template>
  <div v-if="schema?.properties" class="container-lg">
    <div class="row">
      <div class="col-md-8">
        <div :id="`${item_data?.type}-information`" class="form-row">
          <template v-if="firstRowFields.length">
            <div
              v-for="field in firstRowFields"
              :key="field"
              :class="getFieldClass(field, 'first')"
            >
              <label :for="`${item_data?.type}-${field}`">{{
                schema.properties[field]?.title === "Chemform"
                  ? "Chemical Formula"
                  : schema.properties[field]?.title || "Untitled"
              }}</label>
              <component
                :is="getComponentType(field)"
                :id="`${item_data.type}-${field}`"
                v-bind="getComponentProps(field)"
                @update:model-value="handleModelValueUpdate(field, $event)"
                @input="handleInput(field, $event)"
              />
            </div>
          </template>
        </div>

        <div class="form-row">
          <template v-if="secondRowFields.length">
            <div
              v-for="field in secondRowFields"
              :key="field"
              :class="getFieldClass(field, 'second')"
            >
              <label
                v-if="schema.properties[field].title != 'Collections'"
                :for="`${item_data.type}-${field}`"
                >{{ schema.properties[field].title }}</label
              >
              <component
                :is="getComponentType(field)"
                v-if="field == 'collections'"
                :id="`${item_data.type}-${field}`"
                v-bind="getComponentProps(field)"
                v-model="localItemData.collections"
              />
              <component
                :is="getComponentType(field)"
                v-else
                :id="`${item_data.type}-${field}`"
                v-bind="getComponentProps(field)"
                @update:model-value="handleModelValueUpdate(field, $event)"
                @input="handleInput(field, $event)"
              />
            </div>
          </template>
        </div>

        <div v-if="additionalRowFields.length" class="form-row">
          <div
            v-for="field in additionalRowFields"
            :key="field"
            :class="getFieldClass(field, 'additional')"
          >
            <label v-if="field == 'cell_format'" :for="`${item_data.type}-${field}`"
              >Cell format</label
            >
            <label v-else-if="field == 'characteristic_mass'" :for="`${item_data.type}-${field}`"
              >Active mass (mg)</label
            >
            <label
              v-else-if="field == 'characteristic_chemical_formula'"
              :for="`${item_data.type}-${field}`"
            >
              Active formula</label
            >
            <label
              v-else-if="field == 'characteristic_molar_mass'"
              :for="`${item_data.type}-${field}`"
              >Molar mass</label
            >
            <label v-else :for="`${item_data.type}-${field}`">{{
              schema.properties[field]?.title
            }}</label>
            <select
              v-if="field === 'cell_format'"
              :id="`${item_data.type}-${field}`"
              v-model="localItemData.cell_format"
              class="form-control"
              @change="handleModelValueUpdate('cell_format', $event.target.value)"
            >
              <option v-for="format in availableCellFormats" :key="format" :value="format">
                {{ format }}
              </option>
            </select>
            <component
              :is="getComponentType(field)"
              v-else
              :id="`${item_data.type}-${field}`"
              v-bind="getComponentProps(field)"
              @update:model-value="handleModelValueUpdate(field, $event)"
              @input="handleInput(field, $event)"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="col">
            <label :for="`${item_data.type}-description`">Description</label>
            <component
              :is="getComponentType('description')"
              :id="`${item_data.type}-description`"
              v-bind="getComponentProps('description')"
              @update:model-value="handleModelValueUpdate('description', $event)"
            />
          </div>
        </div>
      </div>

      <div v-if="hasRelationships" class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_data.item_id" />
      </div>
    </div>
    <div>
      <TableOfContents
        :item_id="item_data.item_id"
        :information-sections="getTableOfContentsSections()"
      />
    </div>

    <component
      :is="getAdditionalComponent()"
      v-if="getAdditionalComponent()"
      :item_id="item_data.item_id"
      class="mt-3"
    />
  </div>
</template>

<script>
import { getSchema } from "@/server_fetch_utils";
import { cellFormats } from "@/resources.js";

import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import TableOfContents from "@/components/TableOfContents";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import SynthesisInformation from "@/components/SynthesisInformation";
import CellPreparationInformation from "@/components/CellPreparationInformation";

export default {
  components: {
    ItemRelationshipVisualization,
    TableOfContents,
  },
  props: {
    item_data: { type: Object, required: true },
  },
  emits: ["update-item-data"],
  data() {
    return {
      schema: null,
      localItemData: { ...this.item_data },
      availableCellFormats: cellFormats,
    };
  },
  computed: {
    firstRowFields() {
      const commonFields = ["name", "date"];
      const typeSpecificFields = {
        samples: ["chemform"],
        equipments: ["item_id", "refcode"],
        starting_materials: ["chemform", "supplier"],
      };
      return [...commonFields, ...(typeSpecificFields[this.item_data.type] || [])];
    },
    secondRowFields() {
      const commonFields = ["collections"];

      const typeSpecificFields = {
        samples: ["refcode", "creators"],
        cells: ["refcode", "creators"],
        equipments: ["manufacturer", "location"],
        starting_materials: ["refcode", "creators", "collections"],
      };
      return [...(typeSpecificFields[this.item_data.type] || []), ...commonFields];
    },
    additionalRowFields() {
      const typeSpecificFields = {
        cells: [
          "cell_format",
          "cell_format_description",
          "characteristic_mass",
          "characteristic_chemical_formula",
          "characteristic_molar_mass",
        ],
        equipments: ["location", "serial_numbers", "contact"],
        starting_materials: ["CAS", "GHS_codes", "chemical_purity", "location", "date_opened"],
        samples: [],
      };
      return typeSpecificFields[this.item_data.type] || [];
    },
    hasRelationships() {
      return ["samples", "cells"].includes(this.item_data.type);
    },
    tableOfContentsSections() {
      return this.getTableOfContentsSections();
    },
  },
  async mounted() {
    this.schema = await getSchema(this.item_data.type);
  },
  methods: {
    getFieldClass(field) {
      const baseClasses = "form-group";
      const fieldClasses = {
        name: "col-sm-4 pr-2",
        chemform: "col-sm-4 pr-2",
        date: "col-sm-4 pr-2",
        refcode: "d-flex flex-column col-md-3 col-sm-2 col-6",
        creators: "d-flex flex-column col-md-3 col-sm-3 col-6 pb-3",
        collections: "col-md-6 col-sm-7",
        manufacturer: "col-sm-4 pr-2",
        location: "col-lg-3 col-sm-4",
        serial_numbers: "col-md-8",
        contact: "col-md-8",
        CAS: "col-lg-3 col-sm-4",
        GHS_codes: "col-lg-3 col-sm-4",
        chemical_purity: "col-lg-3 col-sm-4",
        cell_format: "col-sm-4 pr-2",
        cell_format_description: "col-sm-8",
        characteristic_mass: "col-lg-3 col-md-4 pr-3",
        characteristic_chemical_formula: "col-lg-4 col-md-4 pr-3",
        characteristic_molar_mass: "col-lg-3 col-md-4",
      };

      return `${baseClasses} ${fieldClasses[field] || "col"}`;
    },
    getComponentType(field) {
      const componentMap = {
        item_id: FormattedItemName,
        collection_id: FormattedCollectionName,
        refcode: FormattedRefcode,
        creators: Creators,
        collections: ToggleableCollectionFormGroup,
        description: TinyMceInline,
        chemform: ChemFormulaInput,
        characteristic_chemical_formula: ChemFormulaInput,
      };
      return componentMap[field] || "input";
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
        case "creators":
          return {
            creators: this.localItemData[field],
            size: "36",
          };
        case "collections":
          return {
            modelValue: this.item_data[field],
            "onUpdate:modelValue": (value) => {
              this.updateField(field, value);
            },
          };
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
    getAdditionalComponent() {
      const componentMap = {
        samples: SynthesisInformation,
        cells: CellPreparationInformation,
      };
      return componentMap[this.item_data.type];
    },
    getTableOfContentsSections() {
      const typeToTitle = {
        samples: "Sample Information",
        cells: "Cell Information",
        equipments: "Equipment Information",
        starting_materials: "Starting Material Information",
      };

      const baseSections = [
        {
          title:
            typeToTitle[this.item_data.type] ||
            `${this.item_data.type.charAt(0).toUpperCase() + this.item_data.type.slice(1)} Information`,
          targetID: `${this.item_data.type}-information`,
        },
        { title: "Table of Contents", targetID: "table-of-contents" },
      ];

      const additionalSections = {
        samples: [{ title: "Synthesis Information", targetID: "synthesis-information" }],
        cells: [{ title: "Cell Construction", targetID: "cell-preparation-information" }],
        starting_materials: [],
        equipments: [],
      };

      return [...baseSections, ...(additionalSections[this.item_data.type] || [])];
    },
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
    handleModelValueUpdate(field, value) {
      this.localItemData[field] = value;

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
  },
};
</script>
