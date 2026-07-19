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
      <template #header>
        <DynamicDataTableButtons
          :data-type="dataType"
          :items-selected="itemsSelected"
          :filters="filters"
          :editable-inventory="editable_inventory"
          :show-buttons="showButtons"
          :available-columns="availableColumns"
          :selected-columns="selectedColumns"
          :collection-id="collectionId"
          :all-users="allUsers"
          @update:filters="updateFilters"
          @update:selected-columns="onToggleColumns"
          @open-create-item-modal="createItemModalIsOpen = true"
          @open-batch-create-item-modal="batchCreateItemModalIsOpen = true"
          @open-qr-scanner-modal="qrScannerModalIsOpen = true"
          @open-create-collection-modal="createCollectionModalIsOpen = true"
          @open-create-equipment-modal="createEquipmentModalIsOpen = true"
          @open-add-to-collection-modal="addToCollectionModalIsOpen = true"
          @open-batch-share-modal="batchShareModalIsOpen = true"
          @delete-selected-items="deleteSelectedItems"
          @remove-selected-items-from-collection="removeSelectedItemsFromCollection"
          @reset-table="handleResetTable"
          @users-data-changed="$emit('users-data-changed')"
          @bulk-invalidate-tokens="handleItemsUpdated"
          @bulk-delete-groups="$emit('groups-data-changed')"
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

      <Column
        v-if="showButtons"
        class="checkbox"
        selection-mode="multiple"
        :style="{ minWidth: '3.5ch' }"
      ></Column>

      <Column
        v-for="column in selectedColumns"
        :key="column.field"
        :field="column.field"
        :sortable="column.sortable !== false"
        :class="{ 'filter-active': isFilterActive(column.field) }"
        :style="{ minWidth: getColumnMinWidth(column) }"
        :filter-menu-class="column.filter && column.filter.noOperator ? 'no-operator' : ''"
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
          <component
            :is="column.body.component"
            v-bind="column.body.props(slotProps.data)"
            v-on="resolveBodyEvents(column)"
          />
        </template>
        <template v-else-if="column.getValue" #body="slotProps">
          {{ column.getValue(slotProps.data) }}
        </template>
        <template v-else #body="slotProps">
          {{ slotProps.data[column.field] }}
        </template>

        <template v-if="column.filter" #filter="{ filterModel, filterCallback }">
          <component
            :is="column.filter.component"
            :model-value="filterModel.value"
            :current-match-mode="filterModel.matchMode"
            :options="filterOptionsCache[column.field] || []"
            v-bind="column.filter.componentProps || {}"
            @update:model-value="filterModel.value = $event"
            @apply="filterCallback()"
            @update:match-mode="
              filterModel.matchMode = $event;
              filterModel.value = null;
            "
          />
        </template>
      </Column>
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
  <BatchShareModal
    v-model="batchShareModalIsOpen"
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
import BatchShareModal from "@/components/BatchShareModal";

import { INVENTORY_TABLE_TYPES, EDITABLE_INVENTORY } from "@/resources.js";

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";
import DataTable from "primevue/datatable";
import Column from "primevue/column";

export default {
  components: {
    DynamicDataTableButtons,
    CreateItemModal,
    BatchCreateItemModal,
    QRScannerModal,
    CreateCollectionModal,
    CreateEquipmentModal,
    AddToCollectionModal,
    BatchShareModal,
    DataTable,
    Column,
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
    collectionId: {
      type: String,
      required: false,
      default: null,
    },
    allUsers: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  emits: ["remove-selected-items-from-collection", "users-data-changed", "groups-data-changed"],
  data() {
    return {
      createItemModalIsOpen: false,
      batchCreateItemModalIsOpen: false,
      qrScannerModalIsOpen: false,
      createCollectionModalIsOpen: false,
      createEquipmentModalIsOpen: false,
      addToCollectionModalIsOpen: false,
      batchShareModalIsOpen: false,
      isSampleFetchError: false,
      itemsSelected: [],
      allSelected: false,
      filters: {},
      filteredData: [],
      allowedTypes: INVENTORY_TABLE_TYPES,
      editable_inventory: EDITABLE_INVENTORY,
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
    adminSuperUserMode() {
      return this.$store.getters.isAdminSuperUserModeActive;
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
    filterOptionsCache() {
      return Object.fromEntries(
        this.columns
          .filter((col) => col.filter?.options && this.data)
          .map((col) => [
            col.field,
            typeof col.filter.options === "function"
              ? col.filter.options(this.data, this.$store.state)
              : col.filter.options,
          ]),
      );
    },
    availableColumns() {
      return this.columns.map((col) => ({ ...col }));
    },
  },
  created() {
    this.$store.commit("setPage", { type: this.dataType, page: 0 });

    const savedState = localStorage.getItem(`datatable-state-${this.dataType}`);
    if (savedState) {
      const parsed = JSON.parse(savedState);
      parsed.first = 0;
      localStorage.setItem(`datatable-state-${this.dataType}`, JSON.stringify(parsed));
    }
    this.selectedColumns = this.availableColumns.filter((col) => !col.hidden);

    FilterService.register("dateBefore", (value, filterValue) => {
      if (!filterValue || !value) return true;
      const itemDate = new Date(value).setHours(0, 0, 0, 0);
      const filterDate = new Date(filterValue).setHours(0, 0, 0, 0);
      return itemDate <= filterDate;
    });
    FilterService.register("dateAfter", (value, filterValue) => {
      if (!filterValue || !value) return true;
      const itemDate = new Date(value).setHours(0, 0, 0, 0);
      const filterDate = new Date(filterValue).setHours(0, 0, 0, 0);
      return itemDate >= filterDate;
    });
    FilterService.register("dateRange", (value, filterValue) => {
      if (!filterValue || !value || !Array.isArray(filterValue) || filterValue.length !== 2)
        return true;
      const itemDate = new Date(value).setHours(0, 0, 0, 0);
      const startDate = new Date(filterValue[0]).setHours(0, 0, 0, 0);
      const endDate = new Date(filterValue[1]).setHours(0, 0, 0, 0);
      return itemDate >= startDate && itemDate <= endDate;
    });

    const filters = { global: { value: null } };
    for (const col of this.columns) {
      if (!col.filter) continue;

      let matchModeName;
      if (typeof col.filter.match === "function") {
        matchModeName = `${this.dataType}_${col.field}`;
        const matchFn = col.filter.match;
        FilterService.register(matchModeName, (value, filterValue) => {
          const operator = this.filters[col.field]?.operator;
          return matchFn(value, filterValue, operator);
        });
      } else {
        matchModeName = col.filter.matchMode || FilterMatchMode.CONTAINS;
      }

      filters[col.field] = {
        operator: col.filter.operator || FilterOperator.AND,
        constraints: [{ value: null, matchMode: matchModeName }],
      };
    }
    this.filters = filters;
  },
  methods: {
    resolveBodyEvents(column) {
      if (!column.body?.events?.length) return {};
      return Object.fromEntries(
        column.body.events.map((event) => [event, (...args) => this.$emit(event, ...args)]),
      );
    },
    getColumnMinWidth(column) {
      const COLUMN_BASE_PADDING = 2.5;
      const CHAR_WIDTH_ESTIMATE = 0.75;
      const SORT_ICON_SPACE = 2.5;
      const FILTER_BUTTON_WIDTH = 3.5;
      const HEADER_ICON_SPACE = 2.5;
      const MIN_COLUMN_WIDTH = 10;

      let minWidth = COLUMN_BASE_PADDING;

      if (column.header) {
        minWidth += column.header.length * CHAR_WIDTH_ESTIMATE;
      }

      if (column.icon) {
        minWidth += HEADER_ICON_SPACE;
      }

      minWidth += SORT_ICON_SPACE;

      if (column.filter) {
        minWidth += FILTER_BUTTON_WIDTH;
      }

      return Math.max(minWidth, MIN_COLUMN_WIDTH) + "ch";
    },
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
    goToEditPage(event) {
      if (this.dataType === "users" || this.dataType === "groups") {
        return;
      }
      const row = event.data;
      let row_id = null;

      event.originalEvent.stopPropagation();
      event.originalEvent.preventDefault();

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
          this.itemsSelected = [...this.itemsSelected, row];
        } else {
          this.itemsSelected = this.itemsSelected.filter((_, i) => i !== selectedIndex);
        }
        return null;
      }

      const clickedElement = event.originalEvent.target;
      const isFormattedCollectionName = clickedElement.closest(" .formatted-collection-name");
      if (isFormattedCollectionName && isFormattedCollectionName.classList.contains("clickable")) {
        return null;
      }

      if (window.Cypress) {
        this.$router.push(`/${this.editPageRoutePrefix}/${row_id}`);
      } else {
        if (event.originalEvent.ctrlKey || event.originalEvent.metaKey) {
          window.open(`/${this.editPageRoutePrefix}/${row_id}`, "_blank");
        } else {
          this.$router.push(`/${this.editPageRoutePrefix}/${row_id}`);
        }
      }
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
        const newItems = itemsToSelect.filter(
          (item) => !selectedIds.has(item.item_id || item.collection_id),
        );
        this.itemsSelected = [...this.itemsSelected, ...newItems];
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
    removeSelectedItemsFromCollection() {
      this.itemsSelected = [];
      this.$emit("remove-selected-items-from-collection");
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

          state.first = 0;

          if (customState.rows) {
            state.rows = customState.rows;
            this.updateRows(customState.rows);
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
        state.first = 0;
        return false;
      }
    },
    updateFilters(newFilters) {
      this.filters = { ...newFilters };
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
