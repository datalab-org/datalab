<template>
  <div class="container">
    <!-- Item information -->
    <div id="equipment-information" class="form-row">
      <div class="form-group col-md-8 col-sm-8">
        <label for="equip-name" class="mr-2">Name</label>
        <input id="equip-name" v-model="Name" class="form-control" />
      </div>
      <div class="form-group col-md-4 col-sm-4">
        <label for="equip-date" class="mr-2">Date</label>
        <input id="equip-date" v-model="EquipmentDate" type="datetime-local" class="form-control" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group col-md-3 col-sm-4">
        <label class="mr-2">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-3 col-sm-3 col-6 pb-3">
        <ToggleableItemStatusFormGroup
          v-model="Status"
          :possible-item-statuses="possibleItemStatuses"
        />
      </div>
      <div class="form-group col-md-3 col-sm-3">
        <label id="collections" class="mr-2">Collections</label>
        <div>
          <CollectionList aria-labelledby="collections" :collections="Collections" />
        </div>
      </div>
      <div class="form-group col-md-3 col-sm-2">
        <label for="equip-item_id" class="mr-2">Item id</label>
        <input id="equip-item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group col-6 pb-3">
        <ToggleableCreatorsFormGroup v-model="Maintainers" :refcode="Refcode" label="Maintainers" />
      </div>
      <div class="form-group col-6 pb-3">
        <ToggleableGroupsFormGroup v-model="ItemGroups" :refcode="Refcode" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group col-md-6">
        <label for="equip-manufacturer" class="mr-2">Manufacturer</label>
        <input id="equip-manufacturer" v-model="Manufacturer" class="form-control" />
      </div>
      <div class="form-group col-md-6">
        <label for="equip-location" class="mr-2">Location</label>
        <LocationInput
          v-model="Location"
          :suggestions="uniqueLocations"
          input-id="equip-location"
        />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-8">
        <label for="equip-serial" class="mr-2">Serial no(s).</label>
        <input id="equip-serial" v-model="SerialNos" class="form-control" />
      </div>
      <div class="form-group col-md-4">
        <label for="equip-contact" class="mr-2">Contact information</label>
        <input id="equip-contact" v-model="Contact" class="form-control" />
      </div>
    </div>
    <label id="equip-description-label" class="mr-2">Description</label>
    <TiptapInline v-model="ItemDescription" aria-labelledby="equip-description-label" />

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :information-sections="tableOfContentsSections"
    />
  </div>
</template>

<script>
import AutoComplete from "primevue/autocomplete";
import { getStartingMaterialList, getEquipmentList } from "@/server_fetch_utils.js";
import { createComputedSetterForItemField } from "@/field_utils.js";
import LocationInput from "@/components/LocationInput";
import TiptapInline from "@/components/TiptapInline";
import TableOfContents from "@/components/TableOfContents";
import CollectionList from "@/components/CollectionList";
import FormattedRefcode from "@/components/FormattedRefcode";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import ToggleableItemStatusFormGroup from "@/components/ToggleableItemStatusFormGroup";
import ToggleableGroupsFormGroup from "@/components/ToggleableGroupsFormGroup";

export default {
  components: {
    AutoComplete,
    TiptapInline,
    CollectionList,
    TableOfContents,
    FormattedRefcode,
    ToggleableCreatorsFormGroup,
    ToggleableItemStatusFormGroup,
    ToggleableGroupsFormGroup,
    LocationInput,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Equipment Information", targetID: "equipment-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
      ],
    };
  },
  computed: {
    item() {
      return this.$store.state.all_item_data[this.item_id];
    },
    ItemDescription: createComputedSetterForItemField("description"),
    Collections: createComputedSetterForItemField("collections"),
    Manufacturer: createComputedSetterForItemField("manufacturer"),
    Name: createComputedSetterForItemField("name"),
    Location: createComputedSetterForItemField("location"),
    Refcode: createComputedSetterForItemField("refcode"),
    EquipmentDate: createComputedSetterForItemField("date"),
    SerialNos: createComputedSetterForItemField("serial_numbers"),
    Maintainers: createComputedSetterForItemField("creators"),
    ItemGroups: createComputedSetterForItemField("groups"),
    Contact: createComputedSetterForItemField("contact"),
    Status: createComputedSetterForItemField("status"),
    schema() {
      return this.$store.state.schemas[this.item?.type];
    },
    possibleItemStatuses() {
      return this.schema?.attributes?.schema?.definitions?.EquipmentStatus?.enum;
    },
    uniqueLocations() {
      return [
        ...new Set(
          [
            ...(this.$store.state.starting_material_list || []),
            ...(this.$store.state.equipment_list || []),
          ]
            .map((item) => item.location)
            .filter(Boolean),
        ),
      ].sort();
    },
  },
  created() {
    if (this.$store.state.starting_material_list === null) {
      getStartingMaterialList();
    }
    if (this.$store.state.equipment_list === null) {
      getEquipmentList();
    }
  },
  methods: {},
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
.badge {
  font-size: 1em;
}
</style>
