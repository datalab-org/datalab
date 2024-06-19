<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      v-model:expandedRows="expandedRows"
      v-on:filter="onFilter"
      :value="samples"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10, 20, 50, 100]"
      filterDisplay="menu"
      :loading="loading"
      :globalFilterFields="[
        'item_id',
        'type',
        'name',
        'chemform',
        'date',
        'collectionsList',
        'creatorsList',
        'nblocks',
      ]"
      removableSort
      sortMode="multiple"
    >
      <template #header>
        <div class="button-group">
          <Button
            label="Delete selected..."
            @click="deleteSelectedItems"
            severity="danger"
            text
            raised
          ></Button>
          <IconField>
            <InputIcon>
              <i class="pi pi-search"></i>
            </InputIcon>
            <InputText v-model="filters['global'].value" placeholder="Search" />
          </IconField>
          <!-- <MultiSelect
            v-model="selectedColumns"
            :options="availableColumns"
            option-label="header"
            option-value="field"
            placeholder="Select columns"
            multiple
          /> -->
        </div>
      </template>
      <template #empty> No samples found. </template>
      <template #loading> Loading samples data. Please wait. </template>

      <Column selectionMode="multiple"></Column>
      <Column expander style="width: 5rem" />
      <Column field="item_id" header="ID" sortable>
        <template #body="slotProps">
          <FormattedItemName
            :item_id="slotProps.data.item_id"
            :itemType="slotProps.data.type"
            enableClick
          />
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <InputText
            v-model="filterModel.value"
            type="text"
            @input="filterCallback()"
            placeholder="Search by ID"
          />
        </template>
        <template> <InputText v-model="filterModel.value" type="text" /> </template>
      </Column>
      <Column field="type" header="Type" sortable>
        <template>
          <InputText v-model="filterModel.value" type="text" />
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

      <template #expansion="slotProps">
        <div class="p-4">
          <h5>Test Expandable {{ slotProps.data.item_id }}</h5>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<script>
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Button from "primevue/button";
// import MultiSelect from "primevue/multiselect";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import { FilterMatchMode } from "@primevue/core/api";
import "primeicons/primeicons.css";

import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import FormattedItemName from "@/components/FormattedItemName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";

export default {
  components: {
    DataTable,
    Column,
    Button,
    // MultiSelect,
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
      selectedColumns: [
        "item_id",
        "type",
        "name",
        "chemform",
        "date",
        "collections",
        "creators",
        "nblocks",
      ],
      filters: {
        global: { value: null },
        item_id: { value: null, matchMode: FilterMatchMode.CONTAINS },
        type: { value: null },
        name: { value: null },
        chemform: { value: null },
        date: { value: null },
        collections: { value: null },
        creators: { value: null },
        nblocks: { value: null },
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
    goToEditPage(params) {
      const row = params.data;
      const event = params.event;
      if (event.ctrlKey || event.metaKey || event.altKey) {
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

.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 1em;
}
</style>
