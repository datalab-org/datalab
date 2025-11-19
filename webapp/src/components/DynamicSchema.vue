<template>
  <div v-if="schema?.properties" class="container-lg">
    <div class="row">
      <div :class="hasRelationships ? 'col-md-8' : 'col-12'">
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
              <div
                v-if="field === 'refcode' || field === 'item_id'"
                :id="`${item_data.type}-${field}`"
              >
                <component :is="getComponentType(field)" v-bind="getComponentProps(field)" />
              </div>
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
              <div v-else-if="field === 'refcode'" :id="`${item_data.type}-${field}`">
                <component :is="getComponentType(field)" v-bind="getComponentProps(field)" />
              </div>

              <div v-else-if="field === 'barcode'" :id="`${item_data.type}-${field}`">
                <component :is="getComponentType(field)" v-bind="getComponentProps(field)" />
              </div>
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

        <template v-if="item_data.type === 'starting_materials' && additionalRowFields.length">
          <div v-if="additionalRowFields.includes('location')" class="form-row">
            <div :class="getFieldClass('location')">
              <label :for="`${item_data.type}-location`">{{
                schema.properties.location?.title
              }}</label>
              <component
                :is="getComponentType('location')"
                :id="`${item_data.type}-location`"
                v-bind="getComponentProps('location')"
                @update:model-value="handleModelValueUpdate('location', $event)"
                @input="handleInput('location', $event)"
              />
            </div>
          </div>

          <div class="form-row">
            <div v-if="additionalRowFields.includes('supplier')" :class="getFieldClass('supplier')">
              <label :for="`${item_data.type}-supplier`">{{
                schema.properties.supplier?.title
              }}</label>
              <component
                :is="getComponentType('supplier')"
                :id="`${item_data.type}-supplier`"
                v-bind="getComponentProps('supplier')"
                @update:model-value="handleModelValueUpdate('supplier', $event)"
                @input="handleInput('supplier', $event)"
              />
            </div>
            <div
              v-if="additionalRowFields.includes('chemical_purity')"
              :class="getFieldClass('chemical_purity')"
            >
              <label :for="`${item_data.type}-chemical_purity`">{{
                schema.properties.chemical_purity?.title
              }}</label>
              <component
                :is="getComponentType('chemical_purity')"
                :id="`${item_data.type}-chemical_purity`"
                v-bind="getComponentProps('chemical_purity')"
                @update:model-value="handleModelValueUpdate('chemical_purity', $event)"
                @input="handleInput('chemical_purity', $event)"
              />
            </div>
          </div>

          <div class="form-row">
            <div v-if="additionalRowFields.includes('CAS')" :class="getFieldClass('CAS')">
              <label :for="`${item_data.type}-CAS`">{{ schema.properties.CAS?.title }}</label>
              <a
                v-if="localItemData.CAS"
                :href="'https://commonchemistry.cas.org/detail?cas_rn=' + localItemData.CAS"
                target="_blank"
              >
                <font-awesome-icon icon="search" class="fixed-width ml-2" />
              </a>
              <component
                :is="getComponentType('CAS')"
                :id="`${item_data.type}-CAS`"
                v-bind="getComponentProps('CAS')"
                @update:model-value="handleModelValueUpdate('CAS', $event)"
                @input="handleInput('CAS', $event)"
              />
            </div>
            <div
              v-if="additionalRowFields.includes('date_opened')"
              :class="getFieldClass('date_opened')"
            >
              <label :for="`${item_data.type}-date_opened`">{{
                schema.properties.date_opened?.title
              }}</label>
              <component
                :is="getComponentType('date_opened')"
                :id="`${item_data.type}-date_opened`"
                v-bind="getComponentProps('date_opened')"
                @update:model-value="handleModelValueUpdate('date_opened', $event)"
                @input="handleInput('date_opened', $event)"
              />
            </div>
          </div>

          <div v-if="additionalRowFields.includes('GHS_codes')" class="form-row">
            <div :class="getFieldClass('GHS_codes')">
              <component
                :is="getComponentType('GHS_codes')"
                v-bind="getComponentProps('GHS_codes')"
                @update:model-value="handleModelValueUpdate('GHS_codes', $event)"
              />
            </div>
          </div>
        </template>

        <div v-else-if="additionalRowFields.length" class="form-row">
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
import FormattedBarcode from "@/components/FormattedBarcode";
import Creators from "@/components/Creators";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import TableOfContents from "@/components/TableOfContents";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import SynthesisInformation from "@/components/SynthesisInformation";
import CellPreparationInformation from "@/components/CellPreparationInformation";
import GHSHazardInformation from "@/components/GHSHazardInformation";

const LAYOUT_CONFIG = {
  firstRow: {
    samples: ["name", "chemform", "date"],
    cells: ["name", "date"],
    equipment: ["refcode", "item_id", "name", "date"],
    starting_materials: ["name", "chemform", "date"],
    collections: ["title"],
  },
  secondRow: {
    samples: ["refcode", "creators", "collections"],
    cells: ["refcode", "creators", "collections"],
    equipment: ["collections", "manufacturer", "location"],
    starting_materials: ["refcode", "barcode", "collections"],
    collections: ["creators"],
  },
  additionalRows: {
    samples: [],
    cells: [
      "cell_format",
      "cell_format_description",
      "characteristic_mass",
      "characteristic_chemical_formula",
      "characteristic_molar_mass",
    ],
    equipment: ["serial_numbers", "creators", "contact"],
    starting_materials: [
      "location",
      "supplier",
      "chemical_purity",
      "CAS",
      "date_opened",
      "GHS_codes",
    ],
    collections: [],
  },
};

const FIELD_WIDTH_MAP = {
  name: "col-sm-4 pr-2 col-6",
  item_id: "col-md-2 col-sm-4",
  refcode: "col-md-3 col-sm-4 col-6",
  barcode: "col-md-3 col-sm-4 col-6",
  chemform: "col-sm-4 pr-2 col-6",
  date: "col-sm-4 col-6",
  manufacturer: "col-md-5",
  supplier: "col-lg-3 col-sm-4",
  location: "col-lg-12 col-sm-12",
  creators: "col-md-3 col-sm-3 col-6 pb-3",
  collections: "col-md-6 col-sm-7 pr-2",
  contact: "col-md-8",
  serial_numbers: "col-md-8",
  CAS: "col-lg-3 col-sm-3 col-6",
  GHS_codes: "col-12",
  chemical_purity: "col-lg-3 col-sm-4",
  cell_format: "col-sm-4",
  cell_format_description: "col-sm-8",
  characteristic_mass: "col-lg-3 col-md-4",
  characteristic_chemical_formula: "col-lg-4 col-md-4",
  characteristic_molar_mass: "col-lg-3 col-md-4",
  date_opened: "col-lg-3 col-sm-3 col-6",
  title: "col",
};

const EQUIPMENT_FIELD_WIDTH_MAP = {
  name: "col-md-6",
  date: "col-md-2",
  refcode: "col-md-2",
  manufacturer: "col-md-5",
  location: "col-md-5",
  collections: "col-md-2",
  serial_numbers: "col-md-8",
  contact: "col-md-8",
  creators: "col-md-4",
};

const SPECIAL_FLEX_FIELDS = {
  creators: true,
};

const COMPONENT_MAP = {
  item_id: FormattedItemName,
  collection_id: FormattedCollectionName,
  refcode: FormattedRefcode,
  barcode: FormattedBarcode,
  creators: Creators,
  collections: ToggleableCollectionFormGroup,
  description: TinyMceInline,
  GHS_codes: GHSHazardInformation,
};

export default {
  components: {
    ItemRelationshipVisualization,
    TableOfContents,
    FormattedItemName,
    FormattedCollectionName,
    FormattedRefcode,
    FormattedBarcode,
    Creators,
    ToggleableCollectionFormGroup,
    TinyMceInline,
    ChemFormulaInput,
    SynthesisInformation,
    CellPreparationInformation,
    GHSHazardInformation,
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
      const fields = LAYOUT_CONFIG.firstRow[this.item_data.type] || ["name", "date"];
      return this.filterExistingFields(fields);
    },
    secondRowFields() {
      const fields = LAYOUT_CONFIG.secondRow[this.item_data.type] || ["collections"];
      return this.filterExistingFields(fields);
    },
    additionalRowFields() {
      const fields = LAYOUT_CONFIG.additionalRows[this.item_data.type] || [];
      return this.filterExistingFields(fields);
    },
    hasRelationships() {
      return ["samples", "cells", "starting_materials", "collections"].includes(
        this.item_data.type,
      );
    },
    tableOfContentsSections() {
      return this.getTableOfContentsSections();
    },
  },
  async mounted() {
    const response = await getSchema(this.item_data.type);
    this.schema = response?.attributes?.schema || response?.attributes || response;
  },
  methods: {
    filterExistingFields(fields) {
      if (!this.schema?.properties) return [];
      return fields.filter((field) => this.schema.properties[field] !== undefined);
    },
    getFieldClass(field) {
      const baseClasses = "form-group";
      const widthMap =
        this.item_data.type === "equipment" ? EQUIPMENT_FIELD_WIDTH_MAP : FIELD_WIDTH_MAP;
      const widthClass = widthMap[field] || FIELD_WIDTH_MAP[field] || "col";

      const needsFlexColumn = SPECIAL_FLEX_FIELDS[field];

      if (needsFlexColumn) {
        return `${baseClasses} d-flex flex-column ${widthClass} ${field === "creators" ? "pb-3" : ""}`;
      }

      return `${baseClasses} ${widthClass} pr-2`;
    },

    getComponentType(field) {
      if (COMPONENT_MAP[field]) {
        return COMPONENT_MAP[field];
      }

      if (field === "chemform" || field.includes("chemical_formula")) {
        return ChemFormulaInput;
      }

      return "input";
    },

    getComponentProps(field) {
      const fieldSchema = this.schema.properties[field];
      if (!fieldSchema) {
        console.warn(`Field schema for "${field}" is missing`);
        return {};
      }

      const componentType = this.getComponentType(field);
      const baseProps = {
        modelValue: this.localItemData[field],
        "onUpdate:modelValue": (value) => this.handleModelValueUpdate(field, value),
      };

      if (componentType === "input") {
        return this.getInputProps(field, fieldSchema);
      }

      return this.getSpecialComponentProps(field, baseProps);
    },

    getInputProps(field, fieldSchema) {
      const value = this.localItemData[field] !== undefined ? this.localItemData[field] : "";

      let inputType = "text";
      if (fieldSchema.type === "date" || fieldSchema.format === "date-time") {
        inputType = "datetime-local";
      } else if (fieldSchema.type === "integer" || fieldSchema.type === "number") {
        inputType = "number";
      }

      return {
        value,
        class: "form-control",
        type: inputType,
      };
    },

    getSpecialComponentProps(field, baseProps) {
      const specialProps = {
        item_id: {
          ...baseProps,
          itemType: this.localItemData.type,
          item_id: this.localItemData.item_id,
          enableClick: true,
        },
        refcode: {
          refcode: this.localItemData.refcode || "",
          enableQRCode: true,
          enableModifiedClick: true,
        },
        barcode: {
          barcode: this.localItemData.barcode || "",
        },
        creators: {
          creators: this.localItemData[field] || [],
          size: "36",
        },
        collections: {
          modelValue: this.item_data[field] || [],
          "onUpdate:modelValue": (value) => this.updateField(field, value),
        },
        GHS_codes: {
          modelValue: Array.isArray(this.localItemData[field])
            ? this.localItemData[field].join(", ")
            : this.localItemData[field] || "",
          "onUpdate:modelValue": (value) => {
            const arrayValue = value
              ? value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
              : [];
            this.handleModelValueUpdate(field, arrayValue);
          },
          editable: true,
        },
        relationships: {
          ...baseProps,
          item_id: this.localItemData.item_id,
        },
      };

      return specialProps[field] || baseProps;
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
        equipment: "Equipment Information",
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
  },
};
</script>
