<template>
  <div class="container-lg">
    <div class="row">
      <div class="col">
        <div id="starting-material-information" class="form-row">
          <div class="form-group col-sm-4 pr-2 col-6">
            <label for="samp-name">Name</label>
            <input id="samp-name" v-model="Name" class="form-control" />
          </div>
          <div class="form-group col-sm-4 pr-2 col-6">
            <label for="startmat-chemform">Chemical formula</label>
            <ChemFormulaInput v-if="isEditable" id="startmat-chemform" v-model="ChemForm" />
            <span v-if="!isEditable" class="form-control-plaintext" readonly>
              <ChemicalFormula id="startmat-chemform" :formula="ChemForm" />
            </span>
          </div>
          <div class="form-group col-sm-4 col-6">
            <label for="startmat-date-acquired">Date acquired</label>
            <StyledInput
              id="startmat-date-acquired"
              v-model="DateAcquired"
              type="datetime-local"
              class="form-control"
              :readonly="!isEditable"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-3 col-sm-4 col-6">
            <label for="startmat-refcode">Refcode</label>
            <div id="startmat-refcode"><FormattedRefcode :refcode="Refcode" /></div>
          </div>
          <div v-if="Barcode" class="form-group col-md-3 col-sm-4 col-6">
            <label for="startmat-barcode">Barcode</label>
            <div id="startmat-barcode"><FormattedBarCode :barcode="Barcode" /></div>
          </div>
          <div class="form-group col-md-4 col-sm-4 col-6">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
          <div class="form-group col-md-5 col-sm-4 col-12">
            <ToggleableItemStatusFormGroup
              v-model="Status"
              :possible-item-statuses="possibleItemStatuses"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-12 col-sm-12">
            <label for="startmat-location">Location</label>
            <AutoComplete
              v-if="isEditable"
              v-model="Location"
              :suggestions="filteredLocations"
              class="form-control p-0 border-0"
              input-class="form-control"
              @complete="filterLocations"
            />
            <StyledInput v-else id="startmat-location" v-model="Location" :readonly="true" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-3 col-sm-4">
            <label for="startmat-supplier">Supplier</label>
            <AutoComplete
              v-if="isEditable"
              v-model="Supplier"
              :suggestions="filteredSuppliers"
              class="form-control p-0 border-0"
              input-class="form-control"
              @complete="filterSuppliers"
            />
            <StyledInput v-else id="startmat-supplier" v-model="Supplier" :readonly="true" />
          </div>
          <div class="form-group col-lg-3 col-sm-4">
            <label for="startmat-purity">Chemical purity</label>
            <StyledInput id="startmat-purity" v-model="ChemicalPurity" :readonly="!isEditable" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-3 col-sm-3 col-6">
            <label for="startmat-cas">CAS</label>
            <a v-if="CAS" :href="'https://commonchemistry.cas.org/detail?cas_rn=' + CAS"
              ><font-awesome-icon icon="search" class="fixed-width ml-2"
            /></a>
            <StyledInput id="startmat-cas" v-model="CAS" :readonly="!isEditable" />
          </div>
          <div class="form-group col-lg-3 col-sm-3 col-6">
            <label for="startmat-date-opened">Date opened</label>
            <StyledInput
              id="startmat-date-opened"
              v-model="DateOpened"
              type="date"
              :readonly="!isEditable"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-12">
            <GHSHazardInformation v-model="GHS" :editable="isEditable" />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TiptapInline v-model="ItemDescription" data-testid="item-description"></TiptapInline>

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :information-sections="tableOfContentsSections"
    />

    <SynthesisInformation class="mt-3" :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import TiptapInline from "@/components/TiptapInline";
import ChemicalFormula from "@/components/ChemicalFormula";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TableOfContents from "@/components/TableOfContents";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import ToggleableItemStatusFormGroup from "@/components/ToggleableItemStatusFormGroup";
import FormattedRefcode from "@/components/FormattedRefcode";
import FormattedBarCode from "@/components/FormattedBarcode";
import StyledInput from "@/components/StyledInput";
import SynthesisInformation from "@/components/SynthesisInformation";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import GHSHazardInformation from "@/components/GHSHazardInformation";

import AutoComplete from "primevue/autocomplete";
import { getStartingMaterialList, getEquipmentList } from "@/server_fetch_utils.js";
import { EDITABLE_INVENTORY } from "@/resources.js";

export default {
  components: {
    AutoComplete,
    StyledInput,
    ChemicalFormula,
    ChemFormulaInput,
    ItemRelationshipVisualization,
    TiptapInline,
    ToggleableCollectionFormGroup,
    ToggleableItemStatusFormGroup,
    TableOfContents,
    FormattedRefcode,
    FormattedBarCode,
    SynthesisInformation,
    GHSHazardInformation,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      filteredSuppliers: [],
      filteredLocations: [],
      tableOfContentsSections: [
        { title: "Starting Material Information", targetID: "starting-material-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
        { title: "Synthesis Information", targetID: "synthesis-information" },
      ],
    };
  },
  computed: {
    item() {
      return this.$store.state.all_item_data[this.item_id];
    },
    ItemID: createComputedSetterForItemField("item_id"),
    Name: createComputedSetterForItemField("name"),
    CAS: createComputedSetterForItemField("CAS"),
    GHS: createComputedSetterForItemField("GHS_codes"),
    DateAcquired: createComputedSetterForItemField("date"),
    DateOpened: createComputedSetterForItemField("date_opened"),
    ChemForm: createComputedSetterForItemField("chemform"),
    Supplier: createComputedSetterForItemField("supplier"),
    ChemicalPurity: createComputedSetterForItemField("chemical_purity"),
    Location: createComputedSetterForItemField("location"),
    ItemDescription: createComputedSetterForItemField("description"),
    Collections: createComputedSetterForItemField("collections"),
    Refcode: createComputedSetterForItemField("refcode"),
    Status: createComputedSetterForItemField("status"),
    schema() {
      return this.$store.state.schemas[this.item?.type];
    },
    possibleItemStatuses() {
      return this.schema?.attributes?.schema?.definitions?.StartingMaterialsStatus?.enum;
    },
    Barcode: createComputedSetterForItemField("barcode"),
    uniqueSuppliers() {
      return [
        ...new Set(
          (this.$store.state.starting_material_list || [])
            .map((item) => item.supplier)
            .filter(Boolean),
        ),
      ].sort();
    },
    uniqueLocations() {
      return [
        ...new Set(
          [
            ...(this.$store.state.starting_material_list || []),
            ...(this.$store.state.equipment_list || []),
          ]
            .map((item) => item.location)
            .filter(Boolean),
        ),
      ].sort();
    },
  },
  created() {
    this.isEditable = EDITABLE_INVENTORY;
    if (this.$store.state.starting_material_list === null) {
      getStartingMaterialList();
    }
    if (this.$store.state.equipment_list === null) {
      getEquipmentList();
    }
  },
  methods: {
    filterSuppliers(event) {
      const query = event.query.toLowerCase();
      this.filteredSuppliers = this.uniqueSuppliers.filter((s) => s.toLowerCase().includes(query));
    },
    filterLocations(event) {
      const query = event.query.toLowerCase();
      this.filteredLocations = this.uniqueLocations.filter((l) => l.toLowerCase().includes(query));
    },
  },
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
