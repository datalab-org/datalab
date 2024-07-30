<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      selection-mode="multiple"
      :value="samples"
      paginator
      :rows="10"
      :rows-per-page-options="[10, 20, 50, 100]"
      filter-display="menu"
      :global-filter-fields="[
        'item_id',
        'type',
        'name',
        'chemform',
        'collectionsList',
        'creatorsList',
        'nblocks',
      ]"
      removable-sort
      sort-mode="multiple"
      @v-on:filter="onFilter"
      @filter="onFilter"
      @row-click="goToEditPage"
    >
      <!-- v-model:expandedRows="expandedRows" -->

      <template #header>
        <div class="button-group d-flex justify-content-between align-items-center">
          <div class="button-left">
            <button class="btn btn-default" @click="createItemModalIsOpen = true">
              Add an item
            </button>
            <button class="btn btn-default ml-2" @click="batchCreateItemModalIsOpen = true">
              Add batch of samples
            </button>
          </div>
          <div class="button-right d-flex">
            <button
              v-if="itemsSelected.length > 0"
              class="btn btn-default ml-2"
              @click="deleteSelectedItems"
            >
              Delete selected
            </button>
            <IconField>
              <InputIcon>
                <i class="pi pi-search"></i>
              </InputIcon>
              <InputText v-model="filters['global'].value" placeholder="Search" />
            </IconField>
          </div>
        </div>
      </template>
      <template #empty> No samples found. </template>
      <template #loading> Loading samples data. Please wait. </template>

      <Column selection-mode="multiple"></Column>
      <!-- <Column expander style="width: 5rem" /> -->
      <Column field="item_id" header="ID" sortable>
        <template #body="slotProps">
          <FormattedItemName
            :item_id="slotProps.data.item_id"
            :item-type="slotProps.data.type"
            enable-click
          />
        </template>
        <template #filter="{ filterModel }">
          <InputText v-model="filterModel.value" type="text" placeholder="Search by ID" />
        </template>
      </Column>
      <Column field="type" header="Type" sortable>
        <template #filter="{ filterModel }">
          <InputText v-model="filterModel.value" type="text" placeholder="Search by type" />
        </template>
      </Column>
      <Column field="name" header="Sample name" sortable> </Column>
      <Column field="chemform" header="Formula" sortable>
        <template #body="slotProps">
          <ChemicalFormula :formula="slotProps.data.chemform" />
        </template>
      </Column>
      <Column field="date" header="Date" sortable>
        <template #body="slotProps">
          {{ $filters.IsoDatetimeToDate(slotProps.data.date) }}
        </template>
      </Column>
      <Column field="collectionsList" header="Collections" sortable>
        <template #body="slotProps">
          <CollectionList :collections="slotProps.data.collections" />
        </template>
      </Column>
      <Column field="creatorsList" header="Creators" sortable>
        <template #body="slotProps">
          <Creators :creators="slotProps.data.creators" />
        </template>
      </Column>
      <Column field="nblocks" header="# of blocks" sortable> ></Column>

      <!-- <template #expansion="slotProps">
        <div class="p-4">
          <h5>Test Expandable {{ slotProps.data.item_id }}</h5>
        </div>
      </template> -->
    </DataTable>
  </div>
  <CreateItemModal v-model="createItemModalIsOpen" />
  <BatchCreateItemModal v-model="batchCreateItemModalIsOpen" />
</template>

<script>
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";

import DataTable from "primevue/datatable";
import Column from "primevue/column";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import { FilterMatchMode, FilterOperator } from "@primevue/core/api";
import "primeicons/primeicons.css";

import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import FormattedItemName from "@/components/FormattedItemName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";

export default {
  components: {
    CreateItemModal,
    BatchCreateItemModal,
    DataTable,
    Column,
    IconField,
    InputIcon,
    InputText,
    FormattedItemName,
    ChemicalFormula,
    CollectionList,
    Creators,
  },
  data() {
    return {
      createItemModalIsOpen: false,
      batchCreateItemModalIsOpen: false,
      isSampleFetchError: false,
      itemsSelected: [],
      expandedRows: [],
      availableColumns: [
        { field: "item_id", header: "ID" },
        { field: "type", header: "Type" },
        { field: "name", header: "Sample name" },
        { field: "chemform", header: "Formula" },
        { field: "date", header: "Date" },
        {
          field: "collections",
          header: "Collections",
        },
        { field: "creators", header: "Creators" },
        { field: "nblocks", header: "# of blocks" },
      ],
      filters: {
        global: { value: null },
        item_id: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
        },
        type: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
        },
      },
    };
  },
  computed: {
    samplesWithComputedFields() {
      return this.$store.state.sample_list.map((sample) => ({
        ...sample,
        collectionsList: sample.collections.map((collection) => collection.collection_id).join(" "),
        creatorsList: sample.creators.map((creator) => creator.display_name).join(" "),
      }));
    },
    samples() {
      return this.samplesWithComputedFields;
    },
  },
  mounted() {
    this.getSamples();
  },
  methods: {
    onFilter: function (event) {
      console.log(event.filteredValue);
    },
    goToEditPage(event) {
      const item_id = event.data.item_id;
      window.open(`/edit/${item_id}`, "_blank");
    },
    getSamples() {
      getSampleList()
        .then(() => {
          console.log("sample list received!");
        })
        .catch(() => {
          this.isSampleFetchError = true;
        });
    },
    applyFilter() {
      this.gridOptions.api.setQuickFilter(this.searchValue);
    },
    onSelectionChanged(event) {
      this.itemsSelected = event.api.getSelectedRows();
    },
    deleteSelectedItems() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected items (${idsSelected})?`,
        )
      ) {
        idsSelected.forEach((item_id) => {
          deleteSample(item_id);
        });
      }
    },
  },
};
</script>

<style>
.customize-table .ag-header {
  font-size: 1rem;
}

.p-datatable-column-header-content .p-datatable-sort-icon {
  visibility: hidden !important;
}
.p-datatable-column-header-content:hover .p-datatable-sort-icon {
  visibility: visible !important;
}

.button-right {
  gap: 0.5em;
}
</style>
