<template>
  <div class="container-lg px-5 px-lg-0">
    <!-- Sample information -->
    <div id="starting-material-information" class="form-row">
      <div class="form-group col-md-2 col-sm-3 col-sm-4">
        <label for="item_id">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-2 col-sm-3 col-sm-4">
        <label for="item_id">Item ID</label>
        <StyledInput id="item_id" readonly :modelValue="ItemID" />
      </div>
      <div class="form-group col-lg-7 col-md-8 col-sm-8">
        <label for="name">Name</label>
        <StyledInput id="name" v-model="Name" :readonly="!isEditable" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-3 col-sm-4">
        <label for="date-acquired" class="mr-2">Date acquired</label>
        <StyledInput
          id="date-acquired"
          type="date"
          v-model="DateAcquired"
          :readonly="!isEditable"
        />
      </div>
      <div class="form-group col-md-3 col-sm-4">
        <label for="date-opened" class="mr-2">Date opened</label>
        <StyledInput id="date-opened" type="date" v-model="DateOpened" :readonly="!isEditable" />
      </div>
      <div class="form-group col-md-6 col-sm-4">
        <label for="location" class="mr-2">Location</label>
        <StyledInput id="location" v-model="Location" :readonly="!isEditable" />
      </div>
    </div>
    <div class="form-row">
      <div class="col-md-3">
        <ToggleableCollectionFormGroup v-model="Collections" />
      </div>
      <div class="form-group col-md-3">
        <label for="chemform" class="mr-2">Chemical formula</label>
        <ChemFormulaInput v-if="isEditable" id="chemform" v-model="ChemForm" />
        <ChemicalFormula v-if="!isEditable" id="chemform" :formula="ChemForm" />
      </div>
      <div class="form-group col-md-3">
        <label for="supplier" class="mr-2">Supplier</label>
        <StyledInput id="supplier" v-model="Supplier" :readonly="!isEditable" />
      </div>
      <div class="form-group col-md-3">
        <label for="purity" class="mr-2">Chemical purity</label>
        <StyledInput id="purity" v-model="ChemicalPurity" :readonly="!isEditable" />
      </div>
    </div>

    <label class="mr-2">Description</label>
    <TinyMceInline v-model="ItemDescription"></TinyMceInline>

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :informationSections="tableOfContentsSections"
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

import { IS_STARTING_MATERIAL_EDITABLE } from "@/resources.js";

export default {
  data() {
    return {
      tableOfContentsSections: [
        { title: "Starting Material Information", targetID: "starting-material-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
      ],
    };
  },
  props: {
    item_id: String,
  },
  computed: {
    item() {
      return this.$store.state.all_item_data[this.item_id];
    },
    ItemID: createComputedSetterForItemField("item_id"),
    Name: createComputedSetterForItemField("name"),
    DateAcquired: createComputedSetterForItemField("date_acquired"),
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
    this.isEditable = IS_STARTING_MATERIAL_EDITABLE;
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
