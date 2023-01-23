<template>
  <div class="container">
    <!-- Sample information -->
    <div id="sample-information" class="form-row">
      <div class="form-group col-md-2">
        <label for="item_id" class="mr-2">Sample ID</label>
        <input id="item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="form-group col-md-7">
        <label for="name" class="mr-2">Name</label>
        <input id="name" class="form-control" v-model="Name" />
      </div>
      <div class="form-group col-md-3">
        <label for="date" class="mr-2">Date Created</label>
        <input type="datetime-local" v-model="DateCreated" class="form-control" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-3">
        <label for="chemform" class="mr-2">Chemical formula</label>
        <ChemFormulaInput id="chemform" v-model="ChemForm" />
      </div>
    </div>
    <label id="description-label" class="mr-2">Description</label>
    <TinyMceInline aria-labelledby="description-label" v-model="SampleDescription"></TinyMceInline>

    <RelationshipVisualization :item_id="item_id" />

    <TableOfContents :item_id="item_id" :informationSections="tableOfContentsSections" />

    <SynthesisInformation class="mt-3" :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TinyMceInline from "@/components/TinyMceInline";
import SynthesisInformation from "@/components/SynthesisInformation";
import TableOfContents from "@/components/TableOfContents";
import RelationshipVisualization from "@/components/RelationshipVisualization";

export default {
  props: {
    item_id: String,
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
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("chemform"),
    DateCreated: createComputedSetterForItemField("date"),
  },
  components: {
    ChemFormulaInput,
    TinyMceInline,
    SynthesisInformation,
    TableOfContents,
    RelationshipVisualization,
  },
};
</script>
