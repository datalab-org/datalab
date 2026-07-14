<template>
  <div class="container-lg">
    <!-- Sample information -->
    <div class="row">
      <div class="col-md-8">
        <div id="sample-information" class="form-row">
          <div class="form-group col-sm-8">
            <label for="cell-name" class="mr-2">Name</label>
            <input id="cell-name" v-model="Name" class="form-control" />
          </div>
          <div class="form-group col-sm-4">
            <label for="cell-date" class="mr-2">Date Created</label>
            <input
              id="cell-date"
              v-model="DateCreated"
              type="datetime-local"
              class="form-control"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-3 col-sm-3 col-3 pr-2">
            <label for="cell-refcode">Refcode</label>
            <div id="cell-refcode">
              <FormattedRefcode :refcode="Refcode" />
            </div>
          </div>
          <div class="form-group col-md-3 col-sm-3 col-3 pr-2">
            <ToggleableItemStatusFormGroup
              v-model="Status"
              :possible-item-statuses="possibleItemStatuses"
            />
          </div>
          <div class="col-md-6 col-6 col-sm-6 pr-2">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-6 pb-3">
            <ToggleableCreatorsFormGroup v-model="ItemCreators" :refcode="Refcode" />
          </div>
          <div class="form-group col-6 pb-3">
            <ToggleableGroupsFormGroup v-model="ItemGroups" :refcode="Refcode" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-4 pr-2">
            <label for="cell-format-dropdown">Cell format</label>
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
          <div class="form-group col-sm-8">
            <label for="cell-format-description">Cell format description</label>
            <input
              id="cell-format-description"
              v-model="CellFormatDescription"
              type="text"
              class="form-control"
            />
          </div>
        </div>

        <div class="form-row py-4">
          <div class="form-group col-lg-3 col-md-4 pr-3">
            <label for="cell-characteristic-mass">Active mass (mg)</label>
            <input
              id="cell-characteristic-mass"
              v-model="CharacteristicMass"
              class="form-control"
              type="text"
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
              v-model="MolarMass"
              class="form-control"
              type="text"
              :class="{ 'red-border': isNaN(MolarMass) }"
            />
          </div>
        </div>
        <div class="form-row py-4">
          <div class="form-group col-lg-4 col-md-4 pr-3">
            <label for="cell-theoretical-capacity">Theoretical capacity</label>
            <div class="input-group">
              <input
                id="cell-theoretical-capacity"
                v-model="TheoreticalCapacity"
                class="form-control"
                type="text"
                :class="{ 'red-border': isNaN(TheoreticalCapacity) }"
              />
              <div class="input-group-append">
                <select v-model="TheoreticalCapacityUnit" class="form-control">
                  <option value="mAh/g">mAh/g</option>
                  <option value="mAh/kg">mAh/kg</option>
                </select>
              </div>
            </div>
          </div>
          <div class="form-group col-lg-4 col-md-4">
            <label
              for="cell-nominal-capacity"
              title="Computed live as theoretical capacity × active mass."
            >
              Nominal capacity
            </label>
            <div class="input-group">
              <div id="cell-nominal-capacity" class="form-control">
                {{ NominalCapacityDisplay }}
              </div>
              <div class="input-group-append">
                <select v-model="NominalCapacityUnit" class="form-control">
                  <option value="mAh">mAh</option>
                  <option value="Ah">Ah</option>
                </select>
              </div>
            </div>
          </div>
        </div>
        <div class="row">
          <div class="col">
            <label id="cell-description-label">Description</label>
            <TiptapInline
              v-model="SampleDescription"
              aria-labelledby="cell-description-label"
            ></TiptapInline>
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
import TiptapInline from "@/components/TiptapInline";
import CellPreparationInformation from "@/components/CellPreparationInformation";
import TableOfContents from "@/components/TableOfContents";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import FormattedRefcode from "@/components/FormattedRefcode";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import ToggleableItemStatusFormGroup from "@/components/ToggleableItemStatusFormGroup";
import ToggleableGroupsFormGroup from "@/components/ToggleableGroupsFormGroup";
import { cellFormats } from "@/resources.js";

export default {
  components: {
    ChemFormulaInput,
    TiptapInline,
    CellPreparationInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    FormattedRefcode,
    ToggleableCollectionFormGroup,
    ToggleableCreatorsFormGroup,
    ToggleableItemStatusFormGroup,
    ToggleableGroupsFormGroup,
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
    item() {
      return this.$store.state.all_item_data[this.item_id];
    },
    Refcode: createComputedSetterForItemField("refcode"),
    ItemID: createComputedSetterForItemField("item_id"),
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    ChemForm: createComputedSetterForItemField("characteristic_chemical_formula"),
    MolarMass: createComputedSetterForItemField("characteristic_molar_mass"),
    DateCreated: createComputedSetterForItemField("date"),
    ItemCreators: createComputedSetterForItemField("creators"),
    ItemGroups: createComputedSetterForItemField("groups"),
    CellFormat: createComputedSetterForItemField("cell_format"),
    CellFormatDescription: createComputedSetterForItemField("cell_format_description"),
    CharacteristicMass: createComputedSetterForItemField("characteristic_mass"),
    Collections: createComputedSetterForItemField("collections"),
    Status: createComputedSetterForItemField("status"),
    TheoreticalCapacity: createComputedSetterForItemField("theoretical_capacity"),
    TheoreticalCapacityUnit: createComputedSetterForItemField("theoretical_capacity_unit"),
    NominalCapacityUnit: createComputedSetterForItemField("nominal_capacity_unit"),
    schema() {
      return this.$store.state.schemas[this.item?.type];
    },
    possibleItemStatuses() {
      return this.schema?.attributes?.schema?.definitions?.CellStatus?.enum;
    },
    // Recomputed live from the store on every render — no save round-trip needed.
    NominalCapacity() {
      const theoreticalCapacityToMahPerG = { "mAh/g": 1, "mAh/kg": 1e-3 };
      const nominalCapacityToMah = { mAh: 1, Ah: 1e3 };

      const theoreticalCapacity = Number(this.TheoreticalCapacity);
      const characteristicMass = Number(this.CharacteristicMass);
      if (!Number.isFinite(theoreticalCapacity) || !Number.isFinite(characteristicMass)) {
        return null;
      }

      const theoreticalCapacityUnit = this.TheoreticalCapacityUnit || "mAh/g";
      const nominalCapacityUnit = this.NominalCapacityUnit || "mAh";

      const mAhPerG = theoreticalCapacity * theoreticalCapacityToMahPerG[theoreticalCapacityUnit];
      // characteristic_mass is stored in mg; divide by 1000 to get grams.
      const mAh = (mAhPerG * characteristicMass) / 1000;
      return mAh / nominalCapacityToMah[nominalCapacityUnit];
    },
    NominalCapacityDisplay() {
      return this.NominalCapacity === null ? "—" : this.NominalCapacity.toFixed(4);
    },
  },
  watch: {
    // Persist the live-computed value too, so it's saved without relying on a
    // server round-trip (the backend validator recomputes it again on save).
    NominalCapacity(value) {
      if (value !== null && value !== this.item?.nominal_capacity) {
        this.$store.commit("updateItemData", {
          item_id: this.item_id,
          item_data: { nominal_capacity: value },
        });
      }
    },
  },
};
</script>
