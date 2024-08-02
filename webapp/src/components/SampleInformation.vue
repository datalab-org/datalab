<template>
  <div class="container-lg">
    <!-- Sample information -->
    <div class="row">
      <div class="col">
        <div id="sample-information" class="form-row">
          <div class="form-group col-sm-4 pr-2">
            <label for="samp-name">Name</label>
            <input id="samp-name" v-model="Name" class="form-control" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="samp-chemform">Chemical formula</label>
            <ChemFormulaInput id="samp-chemform" v-model="ChemForm" />
          </div>
          <div class="form-group col-sm-4 col-6">
            <label for="samp-date">Date Created</label>
            <input
              id="samp-date"
              v-model="DateCreated"
              type="datetime-local"
              class="form-control"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-3 col-sm-2 col-6">
            <label for="samp-refcode">Refcode</label>
            <div id="samp-refcode">
              <FormattedRefcode :refcode="Refcode" />
            </div>
          </div>
          <div class="form-group col-md-3 col-sm-3 col-6 pb-3">
            <ToggleableCreatorsFormGroup v-model="ItemCreators" />
          </div>
          <div class="col-md-6 col-sm-7 pr-2">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>
        <div class="form-row">
          <div class="col">
            <label id="samp-description-label">Description</label>
            <TinyMceInline v-model="SampleDescription" aria-labelledby="samp-description-label" />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <TableOfContents :item_id="item_id" :information-sections="tableOfContentsSections" />

    <SynthesisInformation class="mt-3" :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import FormattedRefcode from "@/components/FormattedRefcode";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import TinyMceInline from "@/components/TinyMceInline";
import SynthesisInformation from "@/components/SynthesisInformation";
import TableOfContents from "@/components/TableOfContents";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";

export default {
  components: {
    ChemFormulaInput,
    TinyMceInline,
    SynthesisInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    FormattedRefcode,
    ToggleableCollectionFormGroup,
    ToggleableCreatorsFormGroup,
  },
  props: {
    item_id: { type: String, required: true },
    refcode: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Sample Information", targetID: "sample-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
        { title: "Synthesis Information", targetID: "synthesis-information" },
      ],
    };
  },
  computed: {
    Refcode: createComputedSetterForItemField("refcode"),
    ItemID: createComputedSetterForItemField("item_id"),
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("chemform"),
    DateCreated: createComputedSetterForItemField("date"),
    ItemCreators: createComputedSetterForItemField("creators"),
    Collections: createComputedSetterForItemField("collections"),
  },
};
</script>
