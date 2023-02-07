<template>
  <div class="container">
    <!-- Sample information -->
    <div id="sample-information" class="form-row">
      <div class="form-group col-md-2">
        <label for="item_id" class="mr-2">Sample ID</label>
        <input id="item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="form-group col-md-6 ml-3">
        <label for="name">Name</label>
        <input id="name" class="form-control" v-model="Name" />
      </div>
      <div class="form-group col-md-3 ml-3">
        <label for="date">Date Created</label>
        <input type="datetime-local" v-model="DateCreated" class="form-control" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-2">
        <label for="cell-format-dropdown" class="mr-2">Cell format</label>
        <select id="cell-format-dropdown" v-model="CellFormat" class="form-control">
          <option
            v-for="(description, key) in availableCellFormats"
            :value="description"
            :key="key"
          >
            {{ description }}
          </option>
        </select>
      </div>
      <div class="form-group col-md-6 ml-3">
        <label for="cell-format-description">Cell description</label>
        <input
          id="cell-format-description"
          type="text"
          class="form-control"
          v-model="CellFormatDescription"
        />
      </div>
    </div>

    <div class="form-row py-4">
      <div class="form-group col-xl-2 col-lg-2 col-md-3">
        <label for="characteristic-mass">Active mass (mg)</label>
        <input
          id="characteristic-mass"
          class="form-control"
          type="text"
          v-model="CharacteristicMass"
          :class="{ 'red-border': isNaN(CharacteristicMass) }"
        />
      </div>
      <div class="form-group col-xl-2 col-lg-3 col-md-4 ml-3">
        <label for="chemform">Active material formula</label>
        <ChemFormulaInput id="chemform" v-model="ChemForm" />
      </div>
      <div class="form-group col-xl-2 col-lg-2 col-md-3 ml-3">
        <label for="characteristic-molar-mass">Molar mass</label>
        <input
          id="characteristic-molar-mass"
          class="form-control"
          type="text"
          v-model="MolarMass"
          :class="{ 'red-border': isNaN(MolarMass) }"
        />
      </div>
    </div>
    <label id="description-label">Description</label>
    <TinyMceInline aria-labelledby="description-label" v-model="SampleDescription"></TinyMceInline>

    <RelationshipVisualization :item_id="item_id" />

    <TableOfContents :item_id="item_id" :informationSections="tableOfContentsSections" />

    <!-- <SynthesisInformation class="mt-3" :item_id="item_id" /> -->
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TinyMceInline from "@/components/TinyMceInline";
// import SynthesisInformation from "@/components/SynthesisInformation";
import TableOfContents from "@/components/TableOfContents";
import RelationshipVisualization from "@/components/RelationshipVisualization";
import { cellFormats } from "@/resources.js";

export default {
  props: {
    item_id: String,
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Sample Information", targetID: "sample-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
        { title: "Cell Information", targetID: "cell-information" },
      ],
      availableCellFormats: cellFormats,
    };
  },
  computed: {
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("characteristic_chemical_formula"),
    MolarMass: createComputedSetterForItemField("characteristic_molar_mass"),
    DateCreated: createComputedSetterForItemField("date"),
    CellFormat: createComputedSetterForItemField("cell_format"),
    CellFormatDescription: createComputedSetterForItemField("cell_format_description"),
    CharacteristicMass: createComputedSetterForItemField("characteristic_mass"),
  },
  components: {
    ChemFormulaInput,
    TinyMceInline,
    // SynthesisInformation,
    TableOfContents,
    RelationshipVisualization,
  },
};
</script>
