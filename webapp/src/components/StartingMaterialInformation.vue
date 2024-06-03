<template>
  <div class="container-lg px-5 px-lg-0">
    <!-- Sample information -->
    <div id="starting-material-information" class="form-row">
      <div class="form-group col-md-2 col-sm-3 col-6">
        <label for="startmat-refcode">Refcode</label>
        <div id="startmat-refcode"><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-2 col-sm-3 col-6">
        <label for="startmat-item_id">Item ID</label>
        <StyledInput id="startmat-item_id" readonly :model-value="ItemID" />
      </div>
      <div class="form-group col-lg-7 col-md-8 col-sm-6">
        <label for="startmat-name">Name</label>
        <StyledInput id="startmat-name" v-model="Name" :readonly="!isEditable" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-chemform">Chemical formula</label>
        <ChemFormulaInput v-if="isEditable" id="startmat-chemform" v-model="ChemForm" />
        <span v-if="!isEditable" class="form-control-plaintext" readonly>
          <ChemicalFormula id="startmat-chemform" :formula="ChemForm" />
        </span>
      </div>
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-supplier">Supplier</label>
        <StyledInput id="startmat-supplier" v-model="Supplier" :readonly="!isEditable" />
      </div>
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-purity">Chemical purity</label>
        <StyledInput id="startmat-purity" v-model="ChemicalPurity" :readonly="!isEditable" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-date-acquired">Date acquired</label>
        <StyledInput
          id="startmat-date-acquired"
          v-model="DateAcquired"
          type="date"
          :readonly="!isEditable"
        />
      </div>
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-date-opened">Date opened</label>
        <StyledInput
          id="startmat-date-opened"
          v-model="DateOpened"
          type="date"
          :readonly="!isEditable"
        />
      </div>
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-location">Location</label>
        <StyledInput id="startmat-location" v-model="Location" :readonly="!isEditable" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-cas">CAS</label>
        <StyledInput id="startmat-cas" v-model="CAS" :readonly="!isEditable" />
      </div>
      <div class="form-group col-lg-3 col-sm-4">
        <label for="startmat-hazards">GHS Hazard Codes</label>
        <StyledInput id="startmat-hazards" v-model="GHS" :readonly="!isEditable" />
      </div>
      <div class="col-lg-3 col-sm-4">
        <ToggleableCollectionFormGroup v-model="Collections" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TinyMceInline v-model="ItemDescription"></TinyMceInline>

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :information-sections="tableOfContentsSections"
    />
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
import StyledInput from "@/components/StyledInput";

import { EDITABLE_INVENTORY } from "@/resources.js";

export default {
  props: {
    item_id: String,
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Starting Material Information", targetID: "starting-material-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
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
  },
  created() {
    this.isEditable = EDITABLE_INVENTORY;
  },
  components: {
    StyledInput,
    ChemicalFormula,
    ChemFormulaInput,
    TinyMceInline,
    ToggleableCollectionFormGroup,
    TableOfContents,
    FormattedRefcode,
  },
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
