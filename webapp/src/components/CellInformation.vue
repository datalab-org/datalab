<template>
  <div class="container-lg">
    <!-- Sample information -->
    <div class="row">
      <div class="col-md-8">
        <div id="sample-information" class="form-row">
          <div class="form-group col-sm-8">
            <label for="cell-name" class="mr-2">Name</label>
            <input id="cell-name" class="form-control" v-model="Name" />
          </div>
          <div class="form-group col-sm-4">
            <label for="cell-date" class="mr-2">Date Created</label>
            <input
              id="cell-date"
              type="datetime-local"
              v-model="DateCreated"
              class="form-control"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-3 col-sm-2 col-6 pr-2">
            <label for="cell-refcode">Refcode</label>
            <div id="cell-refcode">
              <FormattedRefcode :refcode="Refcode" />
            </div>
          </div>
          <div class="form-group col-md-3 col-sm-3 col-6 pb-3 pr-2">
            <label id="cell-creators">Creators</label>
            <div aria-labelledby="cell-creators" class="mx-auto">
              <Creators :creators="ItemCreators" :size="36" />
            </div>
          </div>
          <div class="col-md-6 col-sm-7 pr-2">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-4 pr-2">
            <label for="cell-format-dropdown">Cell format</label>
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
          <div class="form-group col-sm-8">
            <label for="cell-format-description">Cell format description</label>
            <input
              id="cell-format-description"
              type="text"
              class="form-control"
              v-model="CellFormatDescription"
            />
          </div>
        </div>

        <div class="form-row py-4">
          <div class="form-group col-lg-3 col-md-4 pr-3">
            <label for="cell-characteristic-mass">Active mass (mg)</label>
            <input
              id="cell-characteristic-mass"
              class="form-control"
              type="text"
              v-model="CharacteristicMass"
              :class="{ 'red-border': isNaN(CharacteristicMass) }"
            />
          </div>
          <div class="form-group col-lg-4 col-md-4 pr-3">
            <label for="cell-chemform">Active formula</label>
            <ChemFormulaInput id="cell-chemform" v-model="ChemForm" />
          </div>
          <div class="form-group col-lg-3 col-md-4">
            <label for="cell-characteristic-molar-mass">Molar mass</label>
            <input
              id="cell-characteristic-molar-mass"
              class="form-control"
              type="text"
              v-model="MolarMass"
              :class="{ 'red-border': isNaN(MolarMass) }"
            />
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label id="cell-description-label">Description</label>
            <TinyMceInline
              aria-labelledby="cell-description-label"
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
import Creators from "@/components/Creators";
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
  components: {
    ChemFormulaInput,
    TinyMceInline,
    CellPreparationInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    FormattedRefcode,
    ToggleableCollectionFormGroup,
    Creators,
  },
};
</script>
