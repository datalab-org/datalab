<template>
  <div v-if="isSampleFetchError" class="alert alert-danger">
    Server Error. Sample list could not be retreived for collection.
  </div>

  <div class="form-inline mb-2 ml-auto mt-2">
    <div class="form-group">
      <label for="collection-table-search" class="sr-only">Filter items</label>
      <input
        id="collection-table-search"
        type="text"
        class="form-control"
        v-model="searchValue"
        placeholder="Search within collection"
      />
    </div>
    <div class="col-md-6">
      <label id="add-to-collection" class="sr-only">Add items</label>
      <ItemSelect
        id="add-to-collection-select"
        class="select-in-row"
        :modelValue="selectedItemToAdd"
        @update:modelValue="
          selectedItemToAdd = $event;
          addItemFromSearch();
        "
      />
    </div>
  </div>

  <Vue3EasyDataTable
    :headers="headers"
    :items="samples"
    :loading="!sampleTableIsReady"
    :no-hover="true"
    :checkbox-column-width="40"
    :expand-column-width="40"
    :search-value="searchValue"
    table-class-name="customize-table"
    header-class-name="customize-table-header"
    buttons-pagination
    @click-row="goToEditPage"
  >
    <template #empty-message>Collection is empty.</template>

    <template #item-item_id="item">
      <FormattedItemName :item_id="item.item_id" :itemType="item?.type" enableModifiedClick />
    </template>

    <template #item-type="item">
      {{ itemTypes[item.type].display }}
    </template>

    <template #item-chemform="item">
      <ChemicalFormula :formula="item.chemform" />
    </template>

    <template #item-date="item">
      {{ $filters.IsoDatetimeToDate(item.date) }}
    </template>

    <template #item-creators="item">
      <Creators :creators="item.creators" />
    </template>
  </Vue3EasyDataTable>
</template>

<script>
import Vue3EasyDataTable from "vue3-easy-data-table";
import "vue3-easy-data-table/dist/style.css";
import FormattedItemName from "@/components/FormattedItemName";
import ChemicalFormula from "@/components/ChemicalFormula";
import Creators from "@/components/Creators";
import { getCollectionSampleList, addItemToCollection } from "@/server_fetch_utils.js";
import ItemSelect from "@/components/ItemSelect";
// eslint-disable-next-line no-unused-vars
import { itemTypes } from "@/resources.js";

export default {
  props: {
    collection_id: String,
  },
  data() {
    return {
      isSampleFetchError: false,
      itemTypes: itemTypes,
      sampleTableIsReady: false,
      selectedItemToAdd: null,
      itemsSelected: [],
      headers: [
        { text: "ID", value: "item_id", sortable: true },
        { text: "Type", value: "type", sortable: true },
        { text: "Name", value: "name", sortable: true },
        { text: "Formula", value: "chemform", sortable: true },
        { text: "Date", value: "date", sortable: true },
        { text: "Creators", value: "creators", sortable: true },
        { text: "# of blocks", value: "nblocks", sortable: true },
      ],
      searchValue: "",
    };
  },
  computed: {
    samples() {
      return this.$store.state.all_collection_children[this.collection_id] || [];
    },
  },
  methods: {
    addItemFromSearch() {
      if (this.selectedItemToAdd) {
        addItemToCollection(this.selectedItemToAdd, this.collection_id);
      }
    },
    getCollectionSamples() {
      getCollectionSampleList(this.collection_id)
        .then(() => {
          this.sampleTableIsReady = true;
        })
        .catch(() => {
          this.isSampleFetchError = true;
        });
    },
    goToEditPage(row, event) {
      // don't actually go to editpage is this click is in the select column, because
      // that is easy to accidentally do. in future, could try to actuate the checkbox, too.
      if (event.target.querySelector(".easy-checkbox")) {
        return null;
      }
      // if using a modifier key (ctr, meta, alt), open in new tab
      // otherwise, go in this tab
      if (event.ctrl || event.metaKey || event.altKey) {
        window.open(`/edit/${row.item_id}`, "_blank");
      } else {
        this.$router.push(`/edit/${row.item_id}`);
      }
    },
  },
  created() {
    this.getCollectionSamples();
  },
  components: {
    Vue3EasyDataTable,
    ChemicalFormula,
    Creators,
    FormattedItemName,
    ItemSelect,
  },
};
</script>

<style>
.customize-table th {
  --easy-table-row-border: 2px solid #dee2e6;
  border-top: 0.5px solid #dee2e6 !important;
}

.customize-table tr {
  cursor: pointer;
}

.customize-table {
  --easy-table-border: none;
  --easy-table-row-border: 1px solid #dee2e6;
  --easy-table-header-font-size: 1rem;
  --easy-table-body-row-font-size: 1rem;
  --easy-table-footer-font-size: 1rem;
  --easy-table-message-font-size: 1rem;
}

.btn:disabled {
  cursor: not-allowed;
}
</style>
