<template>
  <div class="container-lg">
    <!-- Sample information -->
    <div class="row">
      <div class="col-md-8">
        <div id="sample-information" class="row">
          <div class="mb-3 col-sm-8">
            <label for="cell-name" class="form-label">Name</label>
            <input id="cell-name" v-model="Name" class="form-control" />
          </div>
          <div class="mb-3 col-sm-4">
            <label for="cell-date" class="form-label">Date Created</label>
            <input
              id="cell-date"
              v-model="DateCreated"
              type="datetime-local"
              class="form-control"
            />
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-md-3 col-sm-2 col-6">
            <label for="cell-refcode" class="form-label">Refcode</label>
            <div id="cell-refcode">
              <FormattedRefcode :refcode="Refcode" />
            </div>
          </div>
          <div class="mb-3 col-md-3 col-sm-3 col-6">
            <ToggleableCreatorsFormGroup v-model="ItemCreators" :refcode="Refcode" />
          </div>
          <div class="col-md-6 col-sm-7">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-4">
            <label for="cell-format-dropdown" class="form-label">Cell format</label>
            <select id="cell-format-dropdown" v-model="CellFormat" class="form-control">
              <option
                v-for="(description, key) in availableCellFormats"
                :key="key"
                :value="description"
              >
                {{ description }}
              </option>
            </select>
          </div>
          <div class="mb-3 col-sm-8">
            <label for="cell-format-description" class="form-label">Cell format description</label>
            <input
              id="cell-format-description"
              v-model="CellFormatDescription"
              type="text"
              class="form-control"
            />
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-lg-3 col-md-4">
            <label for="cell-characteristic-mass" class="form-label">Active mass (mg)</label>
            <input
              id="cell-characteristic-mass"
              v-model="CharacteristicMass"
              class="form-control"
              type="text"
              :class="{ 'red-border': isNaN(CharacteristicMass) }"
            />
          </div>
          <div class="mb-3 col-lg-4 col-md-4">
            <label for="cell-chemform" class="form-label">Active formula</label>
            <ChemFormulaInput id="cell-chemform" v-model="ChemForm" />
          </div>
          <div class="mb-3 col-lg-3 col-md-4">
            <label for="cell-characteristic-molar-mass" class="form-label">Molar mass</label>
            <input
              id="cell-characteristic-molar-mass"
              v-model="MolarMass"
              class="form-control"
              type="text"
              :class="{ 'red-border': isNaN(MolarMass) }"
            />
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label id="cell-description-label" class="form-label">Description</label>
            <TinyMceInline
              v-model="SampleDescription"
              aria-labelledby="cell-description-label"
            ></TinyMceInline>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>

    <TableOfContents :item_id="item_id" :information-sections="tableOfContentsSections" />

    <CellPreparationInformation class="mt-3" :item_id="item_id" />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import TinyMceInline from "@/components/TinyMceInline";
import CellPreparationInformation from "@/components/CellPreparationInformation";
import TableOfContents from "@/components/TableOfContents";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import FormattedRefcode from "@/components/FormattedRefcode";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import { cellFormats } from "@/resources.js";

export default {
  components: {
    ChemFormulaInput,
    TinyMceInline,
    CellPreparationInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    FormattedRefcode,
    ToggleableCollectionFormGroup,
    ToggleableCreatorsFormGroup,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Sample Information", targetID: "sample-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
        { title: "Cell Construction", targetID: "cell-preparation-information" },
      ],
      availableCellFormats: cellFormats,
    };
  },
  computed: {
    Refcode: createComputedSetterForItemField("refcode"),
    ItemID: createComputedSetterForItemField("item_id"),
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("characteristic_chemical_formula"),
    MolarMass: createComputedSetterForItemField("characteristic_molar_mass"),
    DateCreated: createComputedSetterForItemField("date"),
    ItemCreators: createComputedSetterForItemField("creators"),
    CellFormat: createComputedSetterForItemField("cell_format"),
    CellFormatDescription: createComputedSetterForItemField("cell_format_description"),
    CharacteristicMass: createComputedSetterForItemField("characteristic_mass"),
    Collections: createComputedSetterForItemField("collections"),
  },
};
</script>
