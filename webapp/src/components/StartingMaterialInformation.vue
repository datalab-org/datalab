<template>
  <div class="container-lg px-5 px-lg-0">
    <div class="row">
      <div class="col-lg-8">
        <!-- Sample information -->
        <div id="starting-material-information" class="row">
          <div class="mb-3 col-md-2 col-sm-4 col-6">
            <label for="startmat-refcode" class="form-label">Refcode</label>
            <div id="startmat-refcode"><FormattedRefcode :refcode="Refcode" /></div>
          </div>
          <div v-if="Barcode" class="mb-3 col-md-2 col-sm-4 col-6">
            <label for="startmat-barcode" class="form-label">Barcode</label>
            <div id="startmat-barcode"><FormattedBarCode :barcode="Barcode" /></div>
          </div>
          <div class="mb-3 col-md-2 col-sm-4 col-6">
            <label for="startmat-item_id" class="form-label">Item ID</label>
            <StyledInput id="startmat-item_id" readonly :model-value="ItemID" />
          </div>
          <div class="mb-3 col-md-6">
            <label for="startmat-name" class="form-label">Name</label>
            <StyledInput id="startmat-name" v-model="Name" :readonly="!isEditable" />
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-md-4">
            <label for="startmat-chemform" class="form-label">Chemical formula</label>
            <ChemFormulaInput v-if="isEditable" id="startmat-chemform" v-model="ChemForm" />
            <span v-if="!isEditable" class="form-control-plaintext" readonly>
              <ChemicalFormula id="startmat-chemform" :formula="ChemForm" />
            </span>
          </div>
          <div class="mb-3 col-md-4">
            <label for="startmat-supplier" class="form-label">Supplier</label>
            <StyledInput id="startmat-supplier" v-model="Supplier" :readonly="!isEditable" />
          </div>
          <div class="mb-3 col-md-4">
            <label for="startmat-purity" class="form-label">Chemical purity</label>
            <StyledInput id="startmat-purity" v-model="ChemicalPurity" :readonly="!isEditable" />
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-md-4">
            <label for="startmat-date-acquired" class="form-label">Date acquired</label>
            <StyledInput
              id="startmat-date-acquired"
              v-model="DateAcquired"
              type="datetime-local"
              :readonly="!isEditable"
            />
          </div>
          <div class="mb-3 col-md-4">
            <label for="startmat-date-opened" class="form-label">Date opened</label>
            <StyledInput
              id="startmat-date-opened"
              v-model="DateOpened"
              type="date"
              :readonly="!isEditable"
            />
          </div>
          <div class="mb-3 col-md-4">
            <label for="startmat-location" class="form-label">Location</label>
            <StyledInput id="startmat-location" v-model="Location" :readonly="!isEditable" />
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-md-4">
            <label for="startmat-cas" class="form-label">CAS</label>
            <a v-if="CAS" :href="'https://commonchemistry.cas.org/detail?cas_rn=' + CAS">
              <font-awesome-icon icon="search" class="fixed-width ms-2" />
            </a>
            <StyledInput id="startmat-cas" v-model="CAS" :readonly="!isEditable" />
          </div>
          <div class="mb-3 col-md-8">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>

        <div class="row mb-3">
          <div class="col-12">
            <GHSHazardInformation v-model="GHS" :editable="isEditable" />
          </div>
        </div>

        <div class="row mb-3">
          <div class="col-12">
            <label class="form-label">Description</label>
            <TinyMceInline v-model="ItemDescription" data-testid="item-description"></TinyMceInline>
          </div>
        </div>

        <TableOfContents
          class="mb-3"
          :item_id="item_id"
          :information-sections="tableOfContentsSections"
        />

        <SynthesisInformation class="mt-3" :item_id="item_id" />
      </div>

      <div class="col-lg-4 mb-3">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import ChemicalFormula from "@/components/ChemicalFormula";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TableOfContents from "@/components/TableOfContents";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import FormattedRefcode from "@/components/FormattedRefcode";
import FormattedBarCode from "@/components/FormattedBarcode";
import StyledInput from "@/components/StyledInput";
import SynthesisInformation from "@/components/SynthesisInformation";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import GHSHazardInformation from "@/components/GHSHazardInformation";

import { EDITABLE_INVENTORY } from "@/resources.js";

export default {
  components: {
    StyledInput,
    ChemicalFormula,
    ChemFormulaInput,
    ItemRelationshipVisualization,
    TinyMceInline,
    ToggleableCollectionFormGroup,
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
    Barcode: createComputedSetterForItemField("barcode"),
  },
  created() {
    this.isEditable = EDITABLE_INVENTORY;
  },
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
