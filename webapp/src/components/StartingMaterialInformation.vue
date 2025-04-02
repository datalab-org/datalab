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
          <div class="form-group col-md-6 col-sm-7 pr-2">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-3 col-sm-4">
            <label for="startmat-supplier">Supplier</label>
            <StyledInput id="startmat-supplier" v-model="Supplier" :readonly="!isEditable" />
          </div>
          <div class="form-group col-lg-3 col-sm-4">
            <label for="startmat-purity">Chemical purity</label>
            <StyledInput id="startmat-purity" v-model="ChemicalPurity" :readonly="!isEditable" />
          </div>
          <div class="form-group col-lg-3 col-sm-4">
            <label for="startmat-location">Location</label>
            <StyledInput id="startmat-location" v-model="Location" :readonly="!isEditable" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-3 col-sm-3 col-6">
            <label for="startmat-cas">CAS</label>
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
            <ToggleableGHSHazardInformation
              v-model="GHS"
              :item_id="item.item_id"
              :type="item.type"
            />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TinyMceInline v-model="ItemDescription" data-testid="item-description"></TinyMceInline>

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
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import ToggleableGHSHazardInformation from "@/components/ToggleableGHSHazardInformation";

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
    ToggleableGHSHazardInformation,
  },
  props: {
    item_id: { type: String, required: true },
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
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
