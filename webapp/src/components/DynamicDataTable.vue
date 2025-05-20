<template>
  <div>
    <div v-if="isSampleFetchError" class="alert alert-danger">
      Server Error. Sample list not retrieved.
    </div>

    <DataTable
      ref="datatable"
      v-model:filters="filters"
      v-model:selection="itemsSelected"
      v-model:select-all="allSelected"
      :value="data"
      :data-testid="computedDataTestId"
      selection-mode="checkbox"
      paginator
      :first="page * rows"
      :rows="rows"
      :rows-per-page-options="[10, 20, 50, 100]"
      filter-display="menu"
      :global-filter-fields="globalFilterFields"
      removable-sort
      column-resize-mode="fit"
      resizable-columns
      sort-mode="multiple"
      state-storage="local"
      :state-key="`datatable-state-${dataType}`"
      :loading="data === null"
      @state-restore="onStateRestore"
      @state-save="onStateSave"
      @filter="onFilter"
      @row-click="goToEditPage"
      @row-select="null"
      @select-all-change="onSelectAllChange"
      @page="onPageChange"
      @sort="onSort"
    >
      <!-- v-model:expandedRows="expandedRows" -->

      <template #header>
        <DynamicDataTableButtons
          :data-type="dataType"
          :items-selected="itemsSelected"
          :filters="filters"
          :editable-inventory="editable_inventory"
          :show-buttons="showButtons"
          :available-columns="availableColumns"
          :selected-columns="selectedColumns"
          @update:filters="updateFilters"
          @update:selected-columns="onToggleColumns"
          @open-create-item-modal="createItemModalIsOpen = true"
          @open-batch-create-item-modal="batchCreateItemModalIsOpen = true"
          @open-qr-scanner-modal="qrScannerModalIsOpen = true"
          @open-create-collection-modal="createCollectionModalIsOpen = true"
          @open-create-equipment-modal="createEquipmentModalIsOpen = true"
          @open-add-to-collection-modal="addToCollectionModalIsOpen = true"
          @delete-selected-items="deleteSelectedItems"
          @reset-table="handleResetTable"
        />
      </template>
      <template #loading>
        <div class="card text-center">
          <div class="card-body">
            <font-awesome-icon
              :icon="['fa', 'sync']"
              class="fa-2x text-primary mb-2"
              :spin="true"
              aria-label="loading"
            />
            <p class="mb-0 font-weight-medium">Loading entries, please wait...</p>
          </div>
        </div>
      </template>
      <template #empty> No entries found. </template>

      <Column v-if="showButtons" class="checkbox" selection-mode="multiple"></Column>

      <!-- <Column expander style="width: 5rem" /> -->
      <Column
        v-for="column in selectedColumns"
        :key="column.field"
        :field="column.field"
        sortable
        :class="{ 'filter-active': isFilterActive(column.field) }"
        :filter-menu-class="column.field === 'type' ? 'no-operator' : ''"
      >
        <template #header>
          <div v-if="column.icon" class="header-with-icon">
            <font-awesome-icon :icon="column.icon" />
            <span v-if="column.header" class="p-datatable-column-title">{{ column.header }}</span>
          </div>
          <template v-else-if="column.header">
            <span class="p-datatable-column-title">{{ column.header }}</span>
          </template>
        </template>

        <template v-if="column.body" #body="slotProps">
          <component :is="column.body" v-bind="getComponentProps(column.body, slotProps.data)" />
        </template>
        <template v-else-if="column.field === 'date'" #body="slotProps">
          {{ $filters.IsoDatetimeToDate(slotProps.data[column.field]) }}
        </template>
        <template v-else #body="slotProps">
          {{ slotProps.data[column.field] }}
        </template>
        <template v-if="column.filter && column.field === 'creators'" #filter>
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="uniqueCreators"
            option-label="display_name"
            placeholder="Any"
            class="d-flex w-full"
            :filter="true"
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

        <template v-else-if="column.filter && column.field === 'collections'" #filter="">
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="uniqueCollections"
            option-label="collection_id"
            placeholder="Any"
            class="d-flex w-full"
            :filter="true"
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
        <template v-else-if="column.filter && column.field === 'type'" #filter="">
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="knownTypes"
            option-label="type"
            placeholder="Select item types"
            class="d-flex w-full"
            :filter="true"
            @click.stop
          >
          </MultiSelect>
        </template>
        <template v-else-if="column.filter && column.body === 'BlocksIconCounter'" #filter>
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="uniqueBlockTypes"
            option-label="type"
            placeholder="Select block types"
            class="d-flex w-full"
            :filter="true"
            @click.stop
          >
            <template #option="slotProps">
              <div class="flex items-center">
                <span>{{ slotProps.option.title }}</span>
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
                    {{ option.title }}
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
import BlocksIconCounter from "@/components/BlocksIconCounter";
import FilesIconCounter from "@/components/FilesIconCounter";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import UserBubble from "@/components/UserBubble.vue";
import FormattedBarcode from "@/components/FormattedBarcode.vue";
import FormattedRefcode from "@/components/FormattedRefcode.vue";

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";
import DataTable from "primevue/datatable";
import MultiSelect from "primevue/multiselect";
import Column from "primevue/column";
import InputText from "primevue/inputtext";

export default {
  components: {
    DynamicDataTableButtons,
    CreateItemModal,
    BlocksIconCounter,
    FilesIconCounter,
    BatchCreateItemModal,
    QRScannerModal,
    FormattedBarcode,
    FormattedRefcode,
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
          constraints: [{ value: null, matchMode: "exactTypeMatch" }],
        },
        location: {
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
        blocks: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "exactBlockMatch" }],
        },
      },
      filteredData: [],
      allowedTypes: INVENTORY_TABLE_TYPES,
      selectedColumns: [],
    };
  },
  computed: {
    rows() {
      return this.$store.state.datatablePaginationSettings[this.dataType].rows;
    },
    page() {
      return this.$store.state.datatablePaginationSettings[this.dataType].page;
    },
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
    uniqueBlockTypes() {
      const itemsWithBlocks = this.data.filter((item) => item.blocks && item.blocks.length > 0);

      const blockTypesMap = new Map(
        itemsWithBlocks
          .flatMap((item) => item.blocks)
          .map((block) => [block.title, { title: block.title }]),
      );

      blockTypesMap.set("No blocks", { title: "No blocks" });

      return Array.from(blockTypesMap.values());
    },
    knownTypes() {
      // Grab the set of types stored under the item type key
      return Array.from(new Set(this.data.map((item) => item.type))).map((type) => ({ type }));
    },
    computedDataTestId() {
      const dataTestIdMap = {
        samples: "sample-table",
        collections: "collection-table",
        startingMaterials: "starting_materials-table",
        equipment: "equipment-table",
      };
      return dataTestIdMap[this.dataType] || "default-table";
    },
    isAllSelected() {
      return this.itemsSelected.length === this.data.length;
    },
    availableColumns() {
      return this.columns.map((col) => ({ ...col }));
    },
  },
  created() {
    this.editable_inventory = EDITABLE_INVENTORY;
    this.selectedColumns = this.availableColumns.filter((col) => !col.hidden);

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
    FilterService.register("exactTypeMatch", (value, filterValue) => {
      if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0)) {
        return true;
      }

      if (Array.isArray(filterValue)) {
        return filterValue.some((f) => f.type === value);
      }

      return filterValue.type === value;
    });
    FilterService.register("exactBlockMatch", (value, filterValue) => {
      if (
        filterValue === null ||
        filterValue === undefined ||
        (Array.isArray(filterValue) && filterValue.length === 0)
      ) {
        return true;
      }

      if (
        Array.isArray(filterValue) &&
        filterValue.some((filter) => filter.title === "No blocks")
      ) {
        if (!value || !Array.isArray(value) || value.length === 0) {
          return true;
        }
      }

      if (!value || !Array.isArray(value)) {
        return false;
      }

      const filter = this.filters.blocks;
      const isAnd = filter && filter.operator === FilterOperator.AND;

      if (Array.isArray(filterValue)) {
        if (isAnd) {
          return filterValue.every((filterBlock) =>
            filterBlock.title === "No blocks"
              ? !value || value.length === 0
              : value.some((itemBlock) => itemBlock.title === filterBlock.title),
          );
        } else {
          return filterValue.some((filterBlock) =>
            filterBlock.title === "No blocks"
              ? !value || value.length === 0
              : value.some((itemBlock) => itemBlock.title === filterBlock.title),
          );
        }
      }

      return value.some((itemBlock) => itemBlock.title === filterValue.title);
    });
  },
  methods: {
    onSort(event) {
      const sortedColumns = event.multiSortMeta || [];

      this.$nextTick(() => {
        const tableHeaders = document.querySelectorAll(".p-datatable-sortable-column");

        tableHeaders.forEach((header) => {
          if (sortedColumns.length === 1) {
            header.classList.add("hide-single-sort-badge");
          } else {
            header.classList.remove("hide-single-sort-badge");
          }
        });
      });

      this.$nextTick(() => {
        this.allSelected = this.checkAllSelected();
      });
    },
    updateFilters(newFilters) {
      this.filters = newFilters;
    },
    goToEditPage(event) {
      const row = event.data;
      let row_id = null;

      event.originalEvent.stopPropagation();
      event.originalEvent.preventDefault();

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

      if (window.Cypress) {
        window.location.href = `/${this.editPageRoutePrefix}/${row_id}`;
      } else {
        window.open(`/${this.editPageRoutePrefix}/${row_id}`, "_blank");
      }
    },
    getComponentProps(componentName, data) {
      const propsConfig = {
        FormattedItemName: {
          item_id: "item_id",
          itemType: "type",
          enableModifiedClick: true,
        },
        FormattedRefcode: {
          enableQRCode: false,
          refcode: "refcode",
        },
        FormattedBarcode: {
          enableBarcode: false,
          enableModifiedClick: false,
          barcode: "barcode",
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
          showNames: data.creators?.length === 1,
        },
        BlocksIconCounter: {
          count: "nblocks",
          blockInfo: "blocks",
        },
        FilesIconCounter: {
          count: "nfiles",
        },
      };

      const config = propsConfig[componentName] || {};

      const props = Object.entries(config).reduce((acc, [prop, setting]) => {
        if (typeof setting === "object" && setting !== null && "value" in setting) {
          acc[prop] = setting.value;
        } else if (typeof setting === "boolean") {
          acc[prop] = setting;
        } else if (typeof setting === "string") {
          if (prop === "itemType") {
            acc[prop] = data.type !== undefined ? data.type : "starting_materials";
          } else if (data[setting] !== undefined) {
            acc[prop] = data[setting];
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
      if (this.$refs.datatable) {
        try {
          return this.$refs.datatable.dataToRender();
        } catch (error) {
          console.error("Error accessing datatable rendered data:", error);
        }
      }
    },
    checkAllSelected() {
      const visibleItems = this.getVisibleItems();

      if (!visibleItems || visibleItems.length === 0) {
        return false;
      }

      return visibleItems.every((currentItem) => {
        const currentId = currentItem.item_id || currentItem.collection_id;
        return this.itemsSelected.some(
          (selectedItem) => (selectedItem.item_id || selectedItem.collection_id) === currentId,
        );
      });
    },
    onFilter(event) {
      this.filteredData = event.filteredValue;
      this.$nextTick(() => {
        this.allSelected = this.checkAllSelected();
      });
    },
    onSelectAllChange(event) {
      this.allSelected = event.checked;
      const itemsToSelect = this.getVisibleItems();

      if (this.allSelected) {
        const selectedIds = new Set(
          this.itemsSelected.map((item) => item.item_id || item.collection_id),
        );

        itemsToSelect.forEach((item) => {
          const itemId = item.item_id || item.collection_id;
          if (!selectedIds.has(itemId)) {
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
    updateRows(rows) {
      this.$store.commit("setRows", { type: this.dataType, rows });
    },
    updatePage(page) {
      this.$store.commit("setPage", { type: this.dataType, page });
    },
    onPageChange(event) {
      this.updatePage(event.page);
      this.updateRows(event.rows);
      this.$nextTick(() => {
        this.allSelected = this.checkAllSelected();
      });
    },
    onToggleColumns(value) {
      this.$nextTick(() => {
        this.selectedColumns = [...value].sort((a, b) => {
          const indexA = this.availableColumns.findIndex((col) => col.field === a.field);
          const indexB = this.availableColumns.findIndex((col) => col.field === b.field);
          return indexA - indexB;
        });
      });
    },
    onStateSave(state) {
      const customState = {
        columnWidths: state.columnWidths,
        visibleColumns: this.selectedColumns.map((col) => col.field),
        first: state.first,
        rows: state.rows,
      };
      localStorage.setItem(`datatable-state-${this.dataType}`, JSON.stringify(customState));

      return false;
    },
    onStateRestore(state) {
      try {
        const savedState = localStorage.getItem(`datatable-state-${this.dataType}`);
        if (savedState) {
          const customState = JSON.parse(savedState);

          if (customState.columnWidths) {
            state.columnWidths = customState.columnWidths;
          }

          if (customState.first) {
            state.first = customState.first;
          }

          if (customState.rows) {
            state.rows = customState.rows;
          }

          if (customState.visibleColumns && Array.isArray(customState.visibleColumns)) {
            this.selectedColumns = this.availableColumns.filter((col) =>
              customState.visibleColumns.includes(col.field),
            );

            if (this.selectedColumns.length === 0) {
              this.selectedColumns = this.availableColumns.filter((col) => !col.hidden);
            }
          }
        }

        return false;
      } catch (error) {
        console.error("Error restoring DataTable state:", error);
        this.selectedColumns = [...this.availableColumns];
        return false;
      }
    },
    handleResetTable() {
      localStorage.removeItem(`datatable-state-${this.dataType}`);

      this.$nextTick(() => {
        location.reload();
      });
    },
  },
};
</script>
