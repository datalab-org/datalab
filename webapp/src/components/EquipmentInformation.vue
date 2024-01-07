<template>
  <div class="container">
    <!-- Item information -->
    <div id="equipment-information" class="form-row">
      <div class="form-group col-md-2 col-sm-4">
        <label for="item_id" class="mr-2">Refcode</label>
        <div><FormattedRefcode :refcode="Refcode" /></div>
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="item_id" class="mr-2">Item id</label>
        <input id="item_id" class="form-control-plaintext" readonly="true" :value="item_id" />
      </div>
      <div class="form-group col-md-6 col-sm-8">
        <label for="name" class="mr-2">Name</label>
        <input id="name" v-model="Name" class="form-control" />
      </div>
      <div class="form-group col-md-2 col-sm-4">
        <label for="datetime-local" class="mr-2">Date</label>
        <input
          type="datetime-local"
          v-model="EquipmentDate"
          id="date-opened"
          class="form-control"
        />
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
        <label for="chemform" class="mr-2">Manufacturer</label>
        <span>
          <input id="Manufacturer" v-model="Manufacturer" class="form-control" />
        </span>
      </div>
      <div class="form-group col-md-5">
        <label for="location" class="mr-2">Location</label>
        <input id="location" v-model="Location" class="form-control" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group col-md-8">
        <label for="serial-input" class="mr-2">Serial no(s).</label>
        <input id="serial-input" v-model="SerialNos" class="form-control" />
      </div>
      <div class="col-md-4 pb-3">
        <label id="maintainers-label" class="mr-2">Maintainers</label>
        <div class="mx-auto">
          <Creators aria-labelledby="maintainers-label" :creators="Maintainers" :size="36" />
        </div>
      </div>
    </div>
    <label class="mr-2">Description</label>
    <TinyMceInline v-model="ItemDescription"></TinyMceInline>

    <TableOfContents
      class="mb-3"
      :item_id="item_id"
      :informationSections="tableOfContentsSections"
    />
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import TableOfContents from "@/components/TableOfContents";
import CollectionList from "@/components/CollectionList";
import FormattedRefcode from "@/components/FormattedRefcode";

export default {
  data() {
    return {
      tableOfContentsSections: [
        { title: "Equipment Information", targetID: "equipment-information" },
        { title: "Table of Contents", targetID: "table-of-contents" },
      ],
    };
  },
  props: {
    item_id: String,
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
  },
  components: {
    TinyMceInline,
    CollectionList,
    TableOfContents,
    FormattedRefcode,
  },
};
</script>

<style scoped>
label {
  font-weight: 500;
  color: #298651;
}
</style>
