<template>
  <div class="container">
    <!-- Sample information -->
    <div class="row">
      <div class="col">
        <div id="sample-information" class="form-row">
          <div class="form-group col-md-4">
            <label for="name" class="mr-2">Name</label>
            <input id="name" class="form-control" v-model="Name" />
          </div>
          <div class="form-group col-md-4">
            <label for="chemform" class="mr-2">Chemical formula</label>
            <ChemFormulaInput id="chemform" v-model="ChemForm" />
          </div>
          <div class="form-group col-md-4">
            <label for="date" class="mr-2">Date Created</label>
            <input
              type="datetime-local"
              v-model="DateCreated"
              class="form-control"
              style="max-width: 250px"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-2">
            <label for="refcode" class="mr-2">Refcode</label>
            <FormattedRefcode :refcode="Refcode" />
          </div>
          <div class="col-md-2 pb-3">
            <label id="creators" class="mr-2">Creators</label>
            <div class="mx-auto">
              <Creators aria-labelledby="creators" :creators="ItemCreators" :size="36" />
            </div>
          </div>
          <div class="form-group col-md">
            <label id="collections" class="mr-2">Collections</label>
            <div>
              <CollectionSelect aria-labelledby="collections" multiple v-model="Collections" />
            </div>
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label id="description-label" class="mr-2">Description</label>
            <TinyMceInline
              aria-labelledby="description-label"
              v-model="SampleDescription"
            ></TinyMceInline>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <TableOfContents :item_id="item_id" :informationSections="tableOfContentsSections" />

    <SynthesisInformation class="mt-3" :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import FormattedRefcode from "@/components/FormattedRefcode";
import CollectionSelect from "@/components/CollectionSelect";
import TinyMceInline from "@/components/TinyMceInline";
import SynthesisInformation from "@/components/SynthesisInformation";
import TableOfContents from "@/components/TableOfContents";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import Creators from "@/components/Creators";

export default {
  props: {
    item_id: String,
    refcode: String,
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
  components: {
    ChemFormulaInput,
    TinyMceInline,
    SynthesisInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    FormattedRefcode,
    CollectionSelect,
    Creators,
  },
};
</script>
