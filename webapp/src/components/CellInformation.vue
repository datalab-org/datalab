<!-- This file was edited with the assistance of an AI model and requires human review from the contributor. -->
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
        <div v-if="enableTags" class="form-row">
          <div class="form-group col-12 pb-3">
            <ToggleableTagsFormGroup v-model="Tags" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-lg-12 col-sm-12">
            <label id="cell-location-label">Location</label>
            <LocationInput
              v-model="Location"
              :hierarchy="$store.getters.getLocationHierarchy"
              input-id="cell-location"
              labelled-by="cell-location-label"
            />
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
          <div class="form-group col-lg-4 col-md-4 pr-3">
            <label for="cell-characteristic-mass">Active mass</label>
            <div class="input-group">
              <input
                id="cell-characteristic-mass"
                v-model="CharacteristicMassInput"
                class="form-control"
                type="text"
                :class="{ 'red-border': isNaN(CharacteristicMassInput) }"
              />
              <div class="input-group-append">
                <select
                  id="cell-characteristic-mass-unit"
                  class="form-control"
                  aria-label="Active mass display unit"
                  :value="displayUnit('characteristic_mass')"
                  @change="setDisplayUnit('characteristic_mass', $event.target.value)"
                >
                  <option
                    v-for="unit in quantities.characteristic_mass.units"
                    :key="unit"
                    :value="unit"
                  >
                    {{ unit }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          <div class="form-group col-lg-4 col-md-4 pr-3">
            <label for="cell-chemform">Active formula</label>
            <ChemFormulaInput id="cell-chemform" v-model="ChemForm" />
          </div>
          <div class="form-group col-lg-3 col-md-4">
            <label for="cell-characteristic-molar-mass">
              Molar mass ({{ quantities.characteristic_molar_mass.canonicalUnit }})
            </label>
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
            <label for="cell-theoretical-capacity">
              Theoretical capacity ({{ quantities.theoretical_capacity.canonicalUnit }})
            </label>
            <input
              id="cell-theoretical-capacity"
              v-model="TheoreticalCapacity"
              class="form-control"
              type="text"
              :class="{ 'red-border': isNaN(TheoreticalCapacity) }"
            />
          </div>
          <div class="form-group col-lg-4 col-md-4">
            <label for="cell-nominal-capacity">
              Nominal capacity
              <a
                v-if="nominalCapacityOverridden"
                href="#"
                class="ml-1"
                title="Reset to the value calculated from theoretical capacity × active mass."
                @click.prevent="resetNominalCapacityToCalculated"
              >
                (reset to calculated)
              </a>
            </label>
            <div class="input-group">
              <input
                id="cell-nominal-capacity"
                v-model="NominalCapacityInput"
                class="form-control"
                type="text"
                :class="{ 'red-border': isNaN(NominalCapacityInput) }"
              />
              <div class="input-group-append">
                <select
                  id="cell-nominal-capacity-unit"
                  class="form-control"
                  aria-label="Nominal capacity display unit"
                  :value="displayUnit('nominal_capacity')"
                  @change="setDisplayUnit('nominal_capacity', $event.target.value)"
                >
                  <option
                    v-for="unit in quantities.nominal_capacity.units"
                    :key="unit"
                    :value="unit"
                  >
                    {{ unit }}
                  </option>
                </select>
              </div>
            </div>
            <small v-if="NominalCapacityMismatchWarning" class="form-text text-warning">
              {{ NominalCapacityMismatchWarning }}
            </small>
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
import ToggleableTagsFormGroup from "@/components/ToggleableTagsFormGroup";
import LocationInput from "@/components/LocationInput";
import { cellFormats } from "@/resources.js";
import { getLocations } from "@/server_fetch_utils.js";
import {
  canonicalOnlyQuantity,
  fromDisplayValue,
  resolveQuantity,
  toDisplayValue,
} from "@/utils/quantities.js";

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
    ToggleableTagsFormGroup,
    LocationInput,
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
      // Display units chosen for quantities that do not persist one with the item.
      localDisplayUnits: {},
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
    Tags: createComputedSetterForItemField("tags"),
    Status: createComputedSetterForItemField("status"),
    TheoreticalCapacity: createComputedSetterForItemField("theoretical_capacity"),
    Location: createComputedSetterForItemField("location"),
    enableTags() {
      return this.$store.state.serverInfo?.features?.tags ?? false;
    },
    schema() {
      return this.$store.state.schemas[this.item?.type];
    },
    possibleItemStatuses() {
      return this.schema?.attributes?.schema?.["$defs"]?.CellStatus?.enum;
    },
    // These fields are always stored in their canonical unit; that unit, the other
    // units they can be displayed in and the conversions between them come from the
    // `datalab_quantity` hints on the cell schema.
    quantities() {
      const properties = this.schema?.attributes?.schema?.properties || {};
      const canonicalUnits = {
        characteristic_mass: "mg",
        characteristic_molar_mass: "g/mol",
        theoretical_capacity: "mAh/g",
        nominal_capacity: "mAh",
      };
      return Object.fromEntries(
        Object.entries(canonicalUnits).map(([field, unit]) => [
          field,
          resolveQuantity(properties[field]) || canonicalOnlyQuantity(unit),
        ]),
      );
    },
    CharacteristicMassInput: {
      get() {
        return this.toDisplay("characteristic_mass", this.CharacteristicMass);
      },
      set(value) {
        this.CharacteristicMass =
          value === "" ? null : this.fromDisplay("characteristic_mass", value);
      },
    },
    // The value that would be calculated from theoretical capacity × active mass, in
    // the canonical unit (mAh). Used to fill the field while no value has been
    // provided, and to tell whether a stored value overrides the calculation.
    CalculatedNominalCapacity() {
      const isMissing = (value) => value === null || value === undefined || value === "";
      if (isMissing(this.TheoreticalCapacity) || isMissing(this.CharacteristicMass)) {
        return null;
      }

      // theoretical_capacity is always mAh/g.
      const theoreticalCapacity = Number(this.TheoreticalCapacity);
      const characteristicMass = Number(this.CharacteristicMass);
      if (!Number.isFinite(theoreticalCapacity) || !Number.isFinite(characteristicMass)) {
        return null;
      }

      // characteristic_mass is stored in mg; divide by 1000 to get grams.
      return (theoreticalCapacity * characteristicMass) / 1000;
    },
    // There is no separate "manual" flag: a stored value overrides the calculation
    // exactly when it differs from it.
    nominalCapacityOverridden() {
      const storedValue = this.item?.nominal_capacity;
      if (storedValue === null || storedValue === undefined) return false;
      if (this.CalculatedNominalCapacity === null) return false;
      return !this.nominalCapacitiesMatch(storedValue, this.CalculatedNominalCapacity);
    },
    NominalCapacityInput: {
      get() {
        const storedValue = this.item?.nominal_capacity;
        if (storedValue !== null && storedValue !== undefined) {
          // A stored value that matches the calculation is shown as the calculation is.
          return this.nominalCapacityOverridden || this.CalculatedNominalCapacity === null
            ? this.toDisplay("nominal_capacity", storedValue)
            : this.displayedCalculatedNominalCapacity;
        }
        return this.displayedCalculatedNominalCapacity;
      },
      set(value) {
        // Clearing the field leaves the value unset, so that it is calculated again.
        const numericValue = value === "" ? null : this.fromDisplay("nominal_capacity", value);
        this.$store.commit("updateItemData", {
          item_id: this.item_id,
          item_data: { nominal_capacity: numericValue },
        });
      },
    },
    // The calculated value in the selected display unit, rounded for display.
    displayedCalculatedNominalCapacity() {
      if (this.CalculatedNominalCapacity === null) return null;
      return Number(this.toDisplay("nominal_capacity", this.CalculatedNominalCapacity).toFixed(4));
    },
    NominalCapacityMismatchWarning() {
      if (!this.nominalCapacityOverridden) {
        return null;
      }
      return `Doesn't match the value calculated from theoretical capacity × active mass (${this.displayedCalculatedNominalCapacity} ${this.displayUnit("nominal_capacity")}).`;
    },
  },
  watch: {
    // The backend only calculates `nominal_capacity` while it is unset, so a stored
    // value that was merely following the calculation is unset again when the
    // calculation changes; otherwise it would go stale and read as an override. A
    // value that already differed from the calculation is an override and is left alone.
    CalculatedNominalCapacity(value, previousValue) {
      const storedValue = this.item?.nominal_capacity;
      if (storedValue === null || storedValue === undefined || previousValue === null) return;
      if (!this.nominalCapacitiesMatch(storedValue, previousValue)) return;
      this.$store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { nominal_capacity: null },
      });
    },
  },
  created() {
    getLocations();
  },
  methods: {
    // The unit a quantity is currently displayed in: the one persisted with the item
    // if the quantity has a display-unit field, otherwise the one chosen in this session.
    displayUnit(field) {
      const quantity = this.quantities[field];
      const unit = quantity.displayUnitField
        ? this.item?.[quantity.displayUnitField]
        : this.localDisplayUnits[field];
      return quantity.units.includes(unit) ? unit : quantity.defaultDisplayUnit;
    },
    // Changing the display unit converts the displayed number; the stored value is unchanged.
    setDisplayUnit(field, unit) {
      const quantity = this.quantities[field];
      if (quantity.displayUnitField) {
        this.$store.commit("updateItemData", {
          item_id: this.item_id,
          item_data: { [quantity.displayUnitField]: unit },
        });
      } else {
        this.localDisplayUnits[field] = unit;
      }
    },
    toDisplay(field, canonicalValue) {
      return toDisplayValue(this.quantities[field], this.displayUnit(field), canonicalValue);
    },
    fromDisplay(field, displayedValue) {
      return fromDisplayValue(this.quantities[field], this.displayUnit(field), displayedValue);
    },
    nominalCapacitiesMatch(a, b) {
      const [x, y] = [Number(a), Number(b)];
      return Math.abs(x - y) <= 1e-6 * Math.max(1, Math.abs(x), Math.abs(y));
    },
    // Unsetting the value leaves it to be calculated again.
    resetNominalCapacityToCalculated() {
      this.$store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { nominal_capacity: null },
      });
    },
  },
};
</script>
