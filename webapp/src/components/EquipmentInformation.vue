<template>
  <div class="container">
    <!-- Item information -->
    <div id="equipment-information" class="form-row">
      <div class="form-group col-md-2 col-sm-4">
        <label class="mr-2">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="equip-item_id" class="mr-2">Item id</label>
        <input id="equip-item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="form-group col-md-6 col-sm-8">
        <label for="equip-name" class="mr-2">Name</label>
        <input id="equip-name" v-model="Name" class="form-control" />
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="equip-date" class="mr-2">Date</label>
        <input id="equip-date" v-model="EquipmentDate" type="datetime-local" class="form-control" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-2">
        <label id="collections" class="mr-2">Collections</label>
        <div>
          <CollectionList aria-labelledby="collections" :collections="Collections" />
        </div>
      </div>
      <div class="form-group col-md-5">
        <label for="equip-manufacturer" class="mr-2">Manufacturer</label>
        <span>
          <input id="equip-manufacturer" v-model="Manufacturer" class="form-control" />
        </span>
      </div>
      <div class="form-group col-md-5">
        <label for="equip-location" class="mr-2">Location</label>
        <input id="equip-location" v-model="Location" class="form-control" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-8">
        <label for="equip-serial" class="mr-2">Serial no(s).</label>
        <input id="equip-serial" v-model="SerialNos" class="form-control" />
      </div>
      <div class="col-md-4 pb-3">
        <label id="equip-maintainers" class="mr-2">Maintainers</label>
        <div class="mx-auto">
          <Creators aria-labelledby="equip-maintainers" :creators="Maintainers" :size="36" />
        </div>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-8">
        <label for="equip-contact" class="mr-2">Contact information</label>
        <input id="equip-contact" v-model="Contact" class="form-control" />
      </div>
    </div>
    <label id="equip-description-label" class="mr-2">Description</label>
    <EditorTransition
      v-model="ItemDescription"
      test-id="item-description-input"
      aria-labelledby="equip-description-label"
    />

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :information-sections="tableOfContentsSections"
    />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import EditorTransition from "@/components/EditorTransition";
import TableOfContents from "@/components/TableOfContents";
import CollectionList from "@/components/CollectionList";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";

export default {
  components: {
    CollectionList,
    TableOfContents,
    FormattedRefcode,
    Creators,
    EditorTransition,
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
    Contact: createComputedSetterForItemField("contact"),
  },
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
