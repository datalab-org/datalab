<template>
  <div class="container">
    <!-- Sample information -->
    <div id="starting-material-information" class="form-row">
      <div class="form-group col-md-2 col-sm-4">
        <label for="item_id" class="mr-2">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="item_id" class="mr-2">Barcode</label>
        <input id="item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="form-group col-md-6 col-sm-8">
        <label for="name" class="mr-2">Name</label>
        <input id="name" :value="item.name" class="form-control-plaintext" readonly="true" />
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="date-opened" class="mr-2">Date acquired</label>
        <input
          id="date-opened"
          :value="$filters.IsoDatetimeToDate(item.date_acquired)"
          class="form-control-plaintext"
          readonly="true"
        />
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="date-opened" class="mr-2">Date opened</label>
        <input
          id="date-opened"
          :value="$filters.IsoDatetimeToDate(item.date_opened)"
          class="form-control-plaintext"
          readonly="true"
        />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-3">
        <label id="collections" class="mr-2">Collections</label>
        <div>
          <CollectionList aria-labelledby="collections" :collections="Collections" />
        </div>
      </div>
      <div class="form-group col-md-3">
        <label for="chemform" class="mr-2">Chemical formula</label>
        <span class="form-control-plaintext" readonly="true">
          <ChemicalFormula :formula="item.chemform" />
        </span>
      </div>
      <div class="form-group col-md-3">
        <label for="supplier" class="mr-2">Supplier</label>
        <input
          id="supplier"
          :value="item.supplier"
          class="form-control-plaintext"
          readonly="true"
        />
      </div>
      <div class="form-group col-md-3">
        <label for="purity" class="mr-2">Chemical purity</label>
        <input
          id="purity"
          :value="item.chemical_purity"
          class="form-control-plaintext"
          readonly="true"
        />
      </div>
    </div>

    <label for="location" class="mr-2">Location</label>
    <input id="location" :value="item.location" class="form-control-plaintext" readonly="true" />

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
import TableOfContents from "@/components/TableOfContents";
import CollectionList from "@/components/CollectionList";
import FormattedRefcode from "@/components/FormattedRefcode";

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
    ItemDescription: createComputedSetterForItemField("description"),
    Collections: createComputedSetterForItemField("collections"),
    Refcode: createComputedSetterForItemField("refcode"),
  },
  components: {
    ChemicalFormula,
    TinyMceInline,
    CollectionList,
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
