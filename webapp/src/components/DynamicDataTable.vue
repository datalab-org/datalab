<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      selection-mode="multiple"
      :value="data"
      paginator
      :rows="20"
      :rows-per-page-options="[10, 20, 50, 100]"
      filter-display="menu"
      :global-filter-fields="globalFilterFields"
      removable-sort
      sort-mode="multiple"
      @row-click="goToEditPage"
    >
      <!-- v-model:expandedRows="expandedRows" -->

      <template #header>
        <DynamicButtonDataTable
          :data-type="dataType"
          :items-selected="itemsSelected"
          :filters="filters"
          :editable-inventory="editable_inventory"
          @open-create-item-modal="createItemModalIsOpen = true"
          @open-batch-create-item-modal="batchCreateItemModalIsOpen = true"
          @open-create-collection-modal="createCollectionModalIsOpen = true"
          @open-create-equipment-modal="createEquipmentModalIsOpen = true"
          @open-add-to-collection-modal="addToCollectionModalIsOpen = true"
          @delete-selected-items="deleteSelectedItems"
        />
      </template>
      <template #empty> No data found. </template>
      <template #loading> Loading data. Please wait. </template>

      <Column selection-mode="multiple"></Column>
      <!-- <Column expander style="width: 5rem" /> -->
      <Column
        v-for="column in columns"
        :key="column.field"
        :field="column.field"
        :header="column.header"
        sortable
      >
        <!-- <template v-if="column.field === 'item_id'" #body="slotProps">
          <component
            :is="column.body"
            v-bind="{
              item_id: slotProps.data.item_id,
              item_type: slotProps.data.type,
              enable_click: true,
            }"
        /></template> -->

        <template v-if="column.body && editable_inventory" #body="slotProps">
          <component :is="column.body" v-bind="getComponentProps(column.body, slotProps.data)" />
        </template>
        <template v-else-if="column.field === 'date'" #body="slotProps">
          {{ $filters.IsoDatetimeToDate(slotProps.data[column.field]) }}
        </template>
        <template v-else #body="slotProps">
          {{ slotProps.data[column.field] }}
        </template>
        <template v-if="column.filter" #filter="{ filterModel }">
          <InputText
            v-model="filterModel.value"
            type="text"
            :placeholder="'Search by ' + column.header"
          />
        </template>
      </Column>

      <!-- <template #expansion="slotProps">
        <div class="p-4">
          <h5>Test Expandable {{ slotProps.data.item_id }}</h5>
        </div>
      </template> -->
    </DataTable>
  </div>
  <CreateItemModal
    v-model="createItemModalIsOpen"
    :allowed-types="dataType == 'startingMaterials' ? allowedTypes : undefined"
  />
  <BatchCreateItemModal v-model="batchCreateItemModalIsOpen" />
  <CreateCollectionModal v-model="createCollectionModalIsOpen" />
  <CreateEquipmentModal v-model="createEquipmentModalIsOpen" />
  <AddToCollectionModal
    v-model="addToCollectionModalIsOpen"
    :items-selected="itemsSelected"
    @items-updated="handleItemsUpdated"
  />
</template>

<script>
import DynamicButtonDataTable from "@/components/DynamicButtonDataTable";
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";
import CreateCollectionModal from "@/components/CreateCollectionModal";
import CreateEquipmentModal from "@/components/CreateEquipmentModal";
import AddToCollectionModal from "@/components/AddToCollectionModal";

import { INVENTORY_TABLE_TYPES, EDITABLE_INVENTORY } from "@/resources.js";

import FormattedItemName from "@/components/FormattedItemName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";

import DataTable from "primevue/datatable";
import Column from "primevue/column";
import InputText from "primevue/inputtext";

export default {
  components: {
    DynamicButtonDataTable,
    CreateItemModal,
    BatchCreateItemModal,
    CreateCollectionModal,
    CreateEquipmentModal,
    AddToCollectionModal,
    DataTable,
    Column,
    InputText,
    FormattedItemName,
    ChemicalFormula,
    CollectionList,
    Creators,
  },
  props: {
    columns: {
      type: Array,
      required: true,
    },
    data: {
      type: Array,
      required: true,
    },
    dataType: {
      type: String,
      required: true,
    },
    globalFilterFields: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      createItemModalIsOpen: false,
      batchCreateItemModalIsOpen: false,
      createCollectionModalIsOpen: false,
      createEquipmentModalIsOpen: false,
      addToCollectionModalIsOpen: false,
      isSampleFetchError: false,
      itemsSelected: [],
      filters: {
        global: { value: null },
      },
      allowedTypes: INVENTORY_TABLE_TYPES,
    };
  },
  created() {
    this.editable_inventory = EDITABLE_INVENTORY;
  },
  methods: {
    goToEditPage(event) {
      const { item_id, collection_id } = event.data;

      if (item_id) {
        window.open(`/edit/${item_id}`, "_blank");
      } else if (collection_id) {
        window.open(`/collections/${collection_id}`, "_blank");
      }
    },
    getComponentProps(componentName, data) {
      const propsConfig = {
        FormattedItemName: {
          item_id: data.item_id !== undefined ? "item_id" : "collection_id",
          itemType: "type",
          enableClick: true,
        },
        ChemicalFormula: {
          formula: "chemform",
        },
        CollectionList: {
          collections: "collections",
        },
        Creators: {
          creators: "creators",
        },
      };

      const config = propsConfig[componentName] || {};

      const props = Object.entries(config).reduce((acc, [prop, dataKey]) => {
        if (dataKey !== true) {
          if (prop === "itemType") {
            acc[prop] = data.type !== undefined ? data.type : "starting_materials";
          } else if (data[dataKey] !== undefined) {
            acc[prop] = data[dataKey];
          }
        }
        return acc;
      }, {});

      Object.keys(config).forEach((prop) => {
        if (config[prop] === true) {
          props[prop] = true;
        }
      });

      return props;
    },
    deleteSelectedItems() {
      this.itemsSelected = [];
    },
    handleItemsUpdated() {
      this.itemsSelected = [];
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

.p-datatable .p-datatable-tbody > tr > td {
  min-width: 1em;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.p-datatable .p-datatable-thead > tr > th {
  min-width: 1em;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.button-right {
  gap: 0.5em;
}
</style>
