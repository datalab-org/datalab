<template>
  <div class="container">
    <!-- Item information -->
    <div id="equipment-information" class="row">
      <div class="mb-3 col-md-2 col-sm-4">
        <label class="form-label">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="mb-3 col-md-2 col-sm-4">
        <label for="equip-item_id" class="form-label">Item id</label>
        <input id="equip-item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="mb-3 col-md-6 col-sm-8">
        <label for="equip-name" class="form-label">Name</label>
        <input id="equip-name" v-model="Name" class="form-control" />
      </div>
      <div class="mb-3 col-md-2 col-sm-4">
        <label for="equip-date" class="form-label">Date</label>
        <input id="equip-date" v-model="EquipmentDate" type="datetime-local" class="form-control" />
      </div>
    </div>
    <div class="row">
      <div class="mb-3 col-md-2">
        <label id="collections" class="form-label">Collections</label>
        <div>
          <CollectionList aria-labelledby="collections" :collections="Collections" />
        </div>
      </div>
      <div class="mb-3 col-md-5">
        <label for="equip-manufacturer" class="form-label">Manufacturer</label>
        <span>
          <input id="equip-manufacturer" v-model="Manufacturer" class="form-control" />
        </span>
      </div>
      <div class="mb-3 col-md-5">
        <label for="equip-location" class="form-label">Location</label>
        <input id="equip-location" v-model="Location" class="form-control" />
      </div>
    </div>
    <div class="row">
      <div class="mb-3 col-md-8">
        <label for="equip-serial" class="form-label">Serial no(s).</label>
        <input id="equip-serial" v-model="SerialNos" class="form-control" />
      </div>
      <div class="col-md-4 pb-3">
        <label id="equip-maintainers" class="form-label">Maintainers</label>
        <div class="mx-auto">
          <Creators aria-labelledby="equip-maintainers" :creators="Maintainers" :size="36" />
        </div>
      </div>
    </div>
    <div class="row">
      <div class="mb-3 col-md-8">
        <label for="equip-contact" class="form-label">Contact information</label>
        <input id="equip-contact" v-model="Contact" class="form-control" />
      </div>
    </div>
    <label id="equip-description-label" class="form-label">Description</label>
    <TinyMceInline v-model="ItemDescription" aria-labelledby="equip-description-label" />

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :information-sections="tableOfContentsSections"
    />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import TableOfContents from "@/components/TableOfContents";
import CollectionList from "@/components/CollectionList";
import FormattedRefcode from "@/components/FormattedRefcode";
import Creators from "@/components/Creators";

export default {
  components: {
    TinyMceInline,
    CollectionList,
    TableOfContents,
    FormattedRefcode,
    Creators,
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
