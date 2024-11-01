<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      v-model:select-all="allSelected"
      :value="data"
      :data-testid="computedDataTestId"
      selection-mode="multiple"
      paginator
      :rows="rows"
      :rows-per-page-options="[10, 20, 50, 100]"
      filter-display="menu"
      :global-filter-fields="globalFilterFields"
      removable-sort
      sort-mode="multiple"
      @filter="onFilter"
      @row-click="goToEditPage"
      @select-all-change="onSelectAllChange"
      @page="onPageChange"
    >
      <!-- v-model:expandedRows="expandedRows" -->

      <template #header>
        <DynamicDataTableButtons
          :data-type="dataType"
          :items-selected="itemsSelected"
          :filters="filters"
          :editable-inventory="editable_inventory"
          :show-buttons="showButtons"
          @open-create-item-modal="createItemModalIsOpen = true"
          @open-batch-create-item-modal="batchCreateItemModalIsOpen = true"
          @open-qr-scanner-modal="qrScannerModalIsOpen = true"
          @open-create-collection-modal="createCollectionModalIsOpen = true"
          @open-create-equipment-modal="createEquipmentModalIsOpen = true"
          @open-add-to-collection-modal="addToCollectionModalIsOpen = true"
          @delete-selected-items="deleteSelectedItems"
        />
      </template>
      <template #empty> No data found. </template>
      <template #loading> Loading data. Please wait. </template>

      <Column v-if="showButtons" class="checkbox" selection-mode="multiple"></Column>

      <!-- <Column expander style="width: 5rem" /> -->
      <Column
        v-for="column in columns"
        :key="column.field"
        :field="column.field"
        :header="column.header"
        sortable
        :class="{ 'filter-active': isFilterActive(column.field) }"
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

        <template v-if="column.body" #body="slotProps">
          <component :is="column.body" v-bind="getComponentProps(column.body, slotProps.data)" />
        </template>
        <template v-else-if="column.field === 'date'" #body="slotProps">
          {{ $filters.IsoDatetimeToDate(slotProps.data[column.field]) }}
        </template>
        <template v-else #body="slotProps">
          {{ slotProps.data[column.field] }}
        </template>
        <template v-if="column.filter && column.field === 'creators'" #filter="{ filterModel }">
          <MultiSelect
            v-model="filterModel.value"
            :options="uniqueCreators"
            option-label="display_name"
            placeholder="Any"
            display="chip"
            class="w-full"
            @click.stop
          >
            <template #option="slotProps">
              <div class="flex items-center">
                <UserBubble :creator="slotProps.option" :size="24" />
                <span class="ml-1">{{ slotProps.option.display_name }}</span>
              </div>
            </template>
            <template #value="slotProps">
              <div class="flex flex-wrap gap-2 items-center">
                <template v-if="slotProps.value && slotProps.value.length">
                  <span
                    v-for="(option, index) in slotProps.value"
                    :key="index"
                    class="inline-flex items-center mr-2"
                  >
                    <UserBubble :creator="option" :size="20" />
                  </span>
                </template>
                <span v-else class="text-gray-400">Any</span>
              </div>
            </template>
          </MultiSelect>
        </template>

        <template
          v-else-if="column.filter && column.field === 'collections'"
          #filter="{ filterModel }"
        >
          <MultiSelect
            v-model="filterModel.value"
            :options="uniqueCollections"
            option-label="collection_id"
            placeholder="Any"
            display="chip"
            class="w-full"
            @click.stop
          >
            <template #option="slotProps">
              <div class="flex items-center">
                <FormattedCollectionName
                  :collection_id="slotProps.option.collection_id"
                  :size="24"
                />
              </div>
            </template>
            <template #value="slotProps">
              <div class="flex flex-wrap gap-1 items-center">
                <template v-if="slotProps.value && slotProps.value.length">
                  <span
                    v-for="option in slotProps.value"
                    :key="option.collection_id"
                    class="inline-flex items-center"
                  >
                    <FormattedCollectionName :collection_id="option.collection_id" :size="20" />
                  </span>
                </template>
                <span v-else class="text-gray-400">Any</span>
              </div>
            </template>
          </MultiSelect>
        </template>
        <template v-else-if="column.filter" #filter="{ filterModel }">
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
  <QRScannerModal v-model="qrScannerModalIsOpen" />
  <CreateCollectionModal v-model="createCollectionModalIsOpen" />
  <CreateEquipmentModal v-model="createEquipmentModalIsOpen" />
  <AddToCollectionModal
    v-model="addToCollectionModalIsOpen"
    :items-selected="itemsSelected"
    @items-updated="handleItemsUpdated"
  />
</template>

<script>
import DynamicDataTableButtons from "@/components/DynamicDataTableButtons";
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";
import QRScannerModal from "@/components/QRScannerModal";
import CreateCollectionModal from "@/components/CreateCollectionModal";
import CreateEquipmentModal from "@/components/CreateEquipmentModal";
import AddToCollectionModal from "@/components/AddToCollectionModal";

import { INVENTORY_TABLE_TYPES, EDITABLE_INVENTORY } from "@/resources.js";

import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import UserBubble from "@/components/UserBubble.vue";

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";
import DataTable from "primevue/datatable";
import MultiSelect from "primevue/multiselect";
import Column from "primevue/column";
import InputText from "primevue/inputtext";

export default {
  components: {
    DynamicDataTableButtons,
    CreateItemModal,
    BatchCreateItemModal,
    QRScannerModal,
    CreateCollectionModal,
    CreateEquipmentModal,
    AddToCollectionModal,
    DataTable,
    MultiSelect,
    Column,
    InputText,
    FormattedItemName,
    FormattedCollectionName,
    ChemicalFormula,
    CollectionList,
    Creators,
    UserBubble,
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
    showButtons: {
      type: Boolean,
      required: false,
      default: true,
    },
    editPageRoutePrefix: {
      type: String,
      required: false,
      default: "edit",
    },
  },
  data() {
    return {
      createItemModalIsOpen: false,
      batchCreateItemModalIsOpen: false,
      qrScannerModalIsOpen: false,
      createCollectionModalIsOpen: false,
      createEquipmentModalIsOpen: false,
      addToCollectionModalIsOpen: false,
      isSampleFetchError: false,
      itemsSelected: [],
      allSelected: false,
      filters: {
        global: { value: null },
        item_id: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
        },
        collection_id: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
        },
        type: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
        },
        collections: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "exactCollectionMatch" }],
        },
        creators: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "exactCreatorMatch" }],
        },
      },
      filteredData: [],
      allowedTypes: INVENTORY_TABLE_TYPES,
      page: 0,
      rows: 20,
    };
  },
  computed: {
    uniqueCreators() {
      return Array.from(
        new Map(
          this.data
            .flatMap((item) => item.creators || [])
            .map((creator) => [JSON.stringify(creator), creator]),
        ).values(),
      );
    },
    uniqueCollections() {
      return Array.from(
        new Map(
          this.data
            .flatMap((item) => item.collections || [])
            .map((collection) => [JSON.stringify(collection.collection_id), collection]),
        ).values(),
      );
    },
    computedDataTestId() {
      const dataTestIdMap = {
        samples: "sample-table",
        collections: "collection-table",
        startingMaterials: "starting-material-table",
        equipment: "equipment-table",
      };
      return dataTestIdMap[this.dataType] || "default-table";
    },
    isAllSelected() {
      return this.itemsSelected.length === this.data.length;
    },
  },
  created() {
    this.editable_inventory = EDITABLE_INVENTORY;

    FilterService.register("exactCollectionMatch", (value, filterValue) => {
      if (!filterValue || !value) return true;

      const filter = this.filters.collections;
      const isAnd = filter.operator === FilterOperator.AND;

      if (Array.isArray(filterValue)) {
        if (isAnd) {
          return filterValue.every((f) =>
            value.some((collection) => collection.collection_id === f.collection_id),
          );
        } else {
          return filterValue.some((f) =>
            value.some((collection) => collection.collection_id === f.collection_id),
          );
        }
      }

      return value.some((collection) => collection.collection_id === filterValue.collection_id);
    });

    FilterService.register("exactCreatorMatch", (value, filterValue) => {
      if (!filterValue || !value) return true;

      const filter = this.filters.creators;
      const isAnd = filter.operator === FilterOperator.AND;

      if (Array.isArray(filterValue)) {
        if (isAnd) {
          return filterValue.every((filterCreator) =>
            value.some((itemCreator) => itemCreator.display_name === filterCreator.display_name),
          );
        } else {
          return filterValue.some((filterCreator) =>
            value.some((itemCreator) => itemCreator.display_name === filterCreator.display_name),
          );
        }
      }

      return value.some((itemCreator) => itemCreator.display_name === filterValue.display_name);
    });
  },
  methods: {
    goToEditPage(event) {
      const row = event.data;
      let row_id = null;

      // Check if the row has an item ID, otherwise default to collection ID
      if (!row.item_id && row.collection_id) {
        row_id = row.collection_id;
      } else {
        row_id = row.item_id;
      }

      if (event.originalEvent.target.classList.contains("checkbox")) {
        return null;
      } else if (event.originalEvent.target.classList.contains("p-checkbox-input")) {
        const selectedIndex = this.itemsSelected.findIndex((item) => item.item_id === row.item_id);

        if (selectedIndex === -1) {
          this.itemsSelected.push(row);
        } else {
          this.itemsSelected.splice(selectedIndex, 1);
        }
        return null;
      }

      if (
        event.originalEvent.ctrlKey ||
        event.originalEvent.metaKey ||
        event.originalEvent.altKey
      ) {
        window.open(`/${this.editPageRoutePrefix}/${row_id}`, "_blank");
      } else {
        this.$router.push(`/${this.editPageRoutePrefix}/${row_id}`);
      }
    },
    getComponentProps(componentName, data) {
      const propsConfig = {
        FormattedItemName: {
          item_id: "item_id",
          itemType: "type",
          enableModifiedClick: true,
        },
        FormattedCollectionName: {
          collection_id: "collection_id",
          enableModifiedClick: true,
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
    isFilterActive(field) {
      const filter = this.filters[field];
      if (filter && filter.constraints) {
        return filter.constraints.some((constraint) => constraint.value);
      }
      return false;
    },
    getVisibleItems() {
      const start = this.page * this.rows;
      const end = start + this.rows;
      if (this.filteredData.length <= this.rows) {
        return this.filteredData.slice(start, end);
      }

      return this.data.slice(start, end);
    },
    checkAllSelected() {
      const visibleItems = this.getVisibleItems();

      if (visibleItems.length === 0) {
        return false;
      }
      return visibleItems.every((currentItem) =>
        this.itemsSelected.some(
          (selectedItem) =>
            (selectedItem.item_id || selectedItem.collection_id) ===
            (currentItem.item_id || currentItem.collection_id),
        ),
      );
    },
    onFilter(event) {
      this.filteredData = event.filteredValue;
      this.allSelected = this.checkAllSelected();
    },
    onSelectAllChange(event) {
      this.allSelected = event.checked;
      const itemsToSelect = this.getVisibleItems();

      if (this.allSelected) {
        const selectedIds = new Set(
          this.itemsSelected.map((item) => item.item_id || item.collection_id),
        );
        itemsToSelect.forEach((item) => {
          if (!selectedIds.has(item.item_id || item.collection_id)) {
            this.itemsSelected.push(item);
          }
        });
      } else {
        const idsToRemove = new Set(
          itemsToSelect.map((item) => item.item_id || item.collection_id),
        );
        this.itemsSelected = this.itemsSelected.filter(
          (item) => !idsToRemove.has(item.item_id || item.collection_id),
        );
      }
    },
    deleteSelectedItems() {
      this.itemsSelected = [];
    },
    handleItemsUpdated() {
      this.itemsSelected = [];
    },
    onPageChange(event) {
      this.page = event.page;
      this.rows = event.rows;
      this.allSelected = this.checkAllSelected();
    },
  },
};
</script>
