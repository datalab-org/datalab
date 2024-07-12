<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      v-on:filter="onFilter"
      :value="samples"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10, 20, 50, 100]"
      filterDisplay="menu"
      :globalFilterFields="[
        'item_id',
        'type',
        'name',
        'chemform',
        'collectionsList',
        'creatorsList',
        'nblocks',
      ]"
      removableSort
      sortMode="multiple"
      @row-click="goToEditPage"
    >
      <!-- v-model:expandedRows="expandedRows" -->

      <template #header>
        <div class="button-group d-flex justify-content-between align-items-center">
          <div class="button-left">
            <button class="btn btn-default" @click="createItemModalIsOpen = true">
              Add an item
            </button>
            <button class="btn btn-default ml-2" @click="batchCreateSampleModalIsOpen = true">
              Add batch of samples
            </button>
          </div>
          <div class="button-right d-flex">
            <Button
              label="Delete selected..."
              @click="deleteSelectedItems"
              severity="danger"
              text
              raised
            ></Button>
            <IconField class="ml-2">
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

      <Column selectionMode="multiple"></Column>
      <!-- <Column expander style="width: 5rem" /> -->
      <Column field="item_id" header="ID" sortable>
        <template #body="slotProps">
          <FormattedItemName
            :item_id="slotProps.data.item_id"
            :itemType="slotProps.data.type"
            enableClick
          />
        </template>
        <template #filter="{ filterModel }">
          <InputText v-model="filterModel.value" type="text" placeholder="Search by ID" />
        </template>
      </Column>
      <Column field="type" header="Type" sortable>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
        <template #filter="{ filterModel }">
          <InputText v-model="filterModel.value" type="text" placeholder="Search by type" />
        </template>
      </Column>
      <Column field="name" header="Sample name" sortable>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
      </Column>
      <Column field="chemform" header="Formula" sortable>
        <template #body="slotProps">
          <ChemicalFormula :formula="slotProps.data.chemform" />
        </template>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
      </Column>
      <Column field="date" header="Date" sortable>
        <template #body="slotProps">
          {{ $filters.IsoDatetimeToDate(slotProps.data.date) }}
        </template>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
      </Column>
      <Column field="collectionsList" header="Collections" sortable>
        <template #body="slotProps">
          <CollectionList :collections="slotProps.data.collections" />
        </template>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
      </Column>
      <Column field="creatorsList" header="Creators" sortable>
        <template #body="slotProps">
          <Creators :creators="slotProps.data.creators" />
        </template>
        <template>
          <InputText v-model="filterModel.value" type="text" />
        </template>
      </Column>
      <Column field="nblocks" header="# of blocks" sortable>
        <template> <InputText v-model="filterModel.value" type="text" /> </template
      ></Column>

      <!-- <template #expansion="slotProps">
        <div class="p-4">
          <h5>Test Expandable {{ slotProps.data.item_id }}</h5>
        </div>
      </template> -->
    </DataTable>
  </div>
  <CreateItemModal v-model="createItemModalIsOpen" />
  <BatchCreateSampleModal v-model="batchCreateSampleModalIsOpen" />
</template>

<script>
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateSampleModal from "@/components/BatchCreateSampleModal";

import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Button from "primevue/button";
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
    BatchCreateSampleModal,
    DataTable,
    Column,
    Button,
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
      batchCreateSampleModalIsOpen: false,
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
          operator: null,
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
  methods: {
    onFilter: function (event) {
      console.log(event.filteredValue);
    },
    goToEditPage(event) {
      const row = event.data;
      if (
        event.originalEvent.ctrlKey ||
        event.originalEvent.metaKey ||
        event.originalEvent.altKey
      ) {
        window.open(`/edit/${row.item_id}`, "_blank");
      } else {
        this.$router.push(`/edit/${row.item_id}`);
      }
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
  mounted() {
    this.getSamples();
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
</style>
