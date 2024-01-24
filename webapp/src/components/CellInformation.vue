<template>
  <div class="container">
    <!-- Sample information -->
    <div class="row">
      <div class="col">
        <div id="sample-information" class="form-row">
          <div class="form-group col-md-5">
            <label for="name" class="mr-2">Name</label>
            <input id="name" class="form-control" v-model="Name" />
          </div>
          <div class="form-group col-md-3">
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
          <div class="form-group col-md-3">
            <label id="collections" class="mr-2">Collections</label>
            <div>
              <CollectionSelect aria-labelledby="collections" multiple v-model="Collections" />
            </div>
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
          <div class="form-group col-md-3">
            <label for="characteristic-mass">Active mass (mg)</label>
            <input
              id="characteristic-mass"
              class="form-control"
              type="text"
              v-model="CharacteristicMass"
              :class="{ 'red-border': isNaN(CharacteristicMass) }"
            />
          </div>
          <div class="form-group col-md-4 ml-3">
            <label for="chemform">Active material formula</label>
            <ChemFormulaInput id="chemform" v-model="ChemForm" />
          </div>
          <div class="form-group col-md-3 ml-3">
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
import CollectionSelect from "@/components/CollectionSelect";
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
    CollectionSelect,
    Creators,
  },
};
</script>
