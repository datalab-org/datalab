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
      :value="tableRows"
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
      :lazy="isGrouped"
      :total-records="isGrouped ? grouped.entries.length : undefined"
      :row-group-mode="isGrouped ? 'subheader' : undefined"
      group-rows-by="__groupKey"
      :row-style="groupHeaderRowStyle"
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
          :displayed-item-count="filteredItemCount"
          :filters="filters"
          :editable-inventory="editable_inventory"
          :show-buttons="showButtons"
          :available-columns="availableColumns"
          :selected-columns="selectedColumns"
          :collection-id="collectionId"
          :all-users="allUsers"
          :group-by-fields="groupByFields"
          @update:filters="updateFilters"
          @update:selected-columns="onToggleColumns"
          @open-create-item-modal="createItemModalIsOpen = true"
          @open-batch-create-item-modal="batchCreateItemModalIsOpen = true"
          @open-qr-scanner-modal="qrScannerModalIsOpen = true"
          @open-create-collection-modal="createCollectionModalIsOpen = true"
          @open-create-equipment-modal="createEquipmentModalIsOpen = true"
          @open-create-tag-modal="$emit('open-create-tag-modal')"
          @open-add-to-collection-modal="addToCollectionModalIsOpen = true"
          @open-batch-share-modal="batchShareModalIsOpen = true"
          @delete-selected-items="deleteSelectedItems"
          @remove-selected-items-from-collection="removeSelectedItemsFromCollection"
          @reset-table="handleResetTable"
          @users-data-changed="$emit('users-data-changed')"
          @bulk-invalidate-tokens="handleItemsUpdated"
          @bulk-delete-groups="$emit('groups-data-changed')"
          @update:result-keys="onResultKeys"
          @update:group-by-fields="groupByFields = $event"
        />
      </template>
      <!-- Shown above the first row of each group on the page: a group header, or a row of a
           group continued from the previous page. -->
      <template #groupheader="{ data: row, index }">
        <DataTableGroupHeader
          :group="grouped.groups.get(row.__groupKey)"
          :expanded="expandedGroups.has(row.__groupKey)"
          :with-parents="index === 0"
          @toggle="toggleGroup(row.__groupKey)"
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
        :selection-mode="isGrouped ? undefined : 'multiple'"
        :style="{ minWidth: '3.5ch' }"
      >
        <!-- Grouped rows are copies of the table's rows, so they select the rows themselves. -->
        <template v-if="isGrouped" #header>
          <Checkbox
            binary
            :model-value="allVisibleRowsSelected"
            aria-label="Select visible rows"
            @update:model-value="selectRows(visibleRows, $event)"
          />
        </template>
        <template v-if="isGrouped" #body="{ data: row }">
          <span v-if="row.__row" @click.stop>
            <Checkbox
              binary
              :model-value="isRowSelected(itemsSelected, row.__row)"
              aria-label="Select row"
              @update:model-value="selectRows([row.__row], $event)"
            />
          </span>
        </template>
      </Column>

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
            v-if="!slotProps.data.group"
            v-bind="column.body.props(slotProps.data)"
            v-on="resolveBodyEvents(column)"
          />
        </template>
        <template v-else-if="column.getValue" #body="slotProps">
          <span v-if="!slotProps.data.group" :class="column.cellClass">
            {{ column.getValue(slotProps.data) }}
          </span>
        </template>
        <template v-else #body="slotProps">
          <span :class="column.cellClass">{{ slotProps.data[column.field] }}</span>
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
import DataTableGroupHeader from "@/components/DataTableGroupHeader";
import CreateItemModal from "@/components/CreateItemModal";
import BatchCreateItemModal from "@/components/BatchCreateItemModal";
import QRScannerModal from "@/components/QRScannerModal";
import CreateCollectionModal from "@/components/CreateCollectionModal";
import CreateEquipmentModal from "@/components/CreateEquipmentModal";
import AddToCollectionModal from "@/components/AddToCollectionModal";
import BatchShareModal from "@/components/BatchShareModal";

import { INVENTORY_TABLE_TYPES, EDITABLE_INVENTORY } from "@/resources.js";
import { rowKey } from "@/utils/tableColumns.js";
import { groupRows, isRowSelected, rowsOfEntries, setRowsSelected } from "@/utils/tableGrouping.js";

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";
import Checkbox from "primevue/checkbox";
import DataTable from "primevue/datatable";
import Column from "primevue/column";

export default {
  components: {
    DynamicDataTableButtons,
    DataTableGroupHeader,
    CreateItemModal,
    BatchCreateItemModal,
    QRScannerModal,
    CreateCollectionModal,
    CreateEquipmentModal,
    AddToCollectionModal,
    BatchShareModal,
    Checkbox,
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
    // The table's `data-testid`; when unset, it is derived from `dataType`.
    testId: {
      type: String,
      required: false,
      default: null,
    },
  },
  emits: [
    "remove-selected-items-from-collection",
    "users-data-changed",
    "groups-data-changed",
    "edit-group",
    "group-deleted",
    "open-create-tag-modal",
  ],
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
      // Names of the per-column matchers this instance registered with the global
      // FilterService, so that they can be removed again when it unmounts.
      registeredMatchModes: [],
      // Keys of the rows matching the advanced search, or null to show every row.
      resultKeys: null,
      groupByFields: [],
      expandedGroups: new Set(),
      // DataTable does not sort grouped tables itself, as it only gets their current page.
      sortMeta: [],
    };
  },

  computed: {
    filteredItemCount() {
      if (this.isGrouped) {
        return this.grouped.rows.length;
      }
      if (this.filteredData === null) {
        return this.data ? this.data.length : 0;
      }
      return this.filteredData.length;
    },
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
      if (this.testId) {
        return this.testId;
      }
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
    displayedData() {
      if (!this.data || !this.resultKeys) return this.data;
      return this.data.filter((row) => this.resultKeys.has(rowKey(row)));
    },
    isGrouped() {
      return this.groupByFields.length > 0;
    },
    // The rows of a grouped table, and the group headers and rows it shows (see `groupRows`).
    grouped() {
      if (!this.isGrouped || !this.displayedData)
        return { rows: [], entries: [], groups: new Map() };
      return groupRows(this.displayedData, this.groupByFields, {
        filters: this.filters,
        globalFilterFields: this.globalFilterFields,
        sortMeta: this.sortMeta,
        expandedKeys: this.expandedGroups,
      });
    },
    tableRows() {
      if (!this.isGrouped) return this.displayedData;
      return this.grouped.entries.slice(this.page * this.rows, (this.page + 1) * this.rows);
    },
    visibleRows() {
      return rowsOfEntries(this.tableRows || []);
    },
    allVisibleRowsSelected() {
      return (
        this.visibleRows.length > 0 &&
        this.visibleRows.every((row) => isRowSelected(this.itemsSelected, row))
      );
    },
  },
  watch: {
    // DataTable only reports its filtered rows (@filter) when its filters change, so also take
    // them from it when the rows it is given change, e.g. after an advanced search.
    displayedData() {
      this.refreshFilteredData();
    },
    groupByFields() {
      this.expandedGroups = new Set();
      this.updatePage(0);
      this.refreshFilteredData();
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
        this.registeredMatchModes.push(matchModeName);
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
  unmounted() {
    // These matchers close over this instance, so drop them rather than leaving them
    // in the global FilterService registry once the table is gone.
    for (const matchModeName of this.registeredMatchModes) {
      delete FilterService.filters[matchModeName];
    }
    this.registeredMatchModes = [];
  },
  methods: {
    isRowSelected,
    onResultKeys(keys) {
      this.resultKeys = keys;
      this.updatePage(0);
    },
    toggleGroup(key) {
      const expanded = new Set(this.expandedGroups);
      if (!expanded.delete(key)) expanded.add(key);
      this.expandedGroups = expanded;
      // Collapsing a group can leave fewer pages than the current one.
      const lastPage = Math.max(Math.ceil(this.grouped.entries.length / this.rows) - 1, 0);
      if (this.page > lastPage) this.updatePage(lastPage);
    },
    selectRows(rows, selected) {
      this.itemsSelected = setRowsSelected(this.itemsSelected, rows, selected);
    },
    // A group header's own row only carries the header, which DataTable shows above it.
    groupHeaderRowStyle(row) {
      return row.group ? { display: "none" } : undefined;
    },
    refreshFilteredData() {
      this.$nextTick(() => {
        this.filteredData = this.$refs.datatable?.processedData ?? this.displayedData ?? [];
      });
    },
    resolveBodyEvents(column) {
      const listeners = Object.fromEntries(
        (column.body?.events || []).map((event) => [
          event,
          (...args) => this.$emit(event, ...args),
        ]),
      );
      // Events that set this column's own filter (e.g. clicking a value in a cell to show
      // only the rows sharing it), each mapping the event payload to the filter value.
      for (const [event, toFilterValue] of Object.entries(column.body?.filterEvents || {})) {
        listeners[event] = (payload) => this.setColumnFilter(column.field, toFilterValue(payload));
      }
      return listeners;
    },
    setColumnFilter(field, value) {
      const filter = this.filters[field];
      if (!filter?.constraints) return;
      // Replace the `filters` reference so the DataTable reliably re-applies the
      // menu-mode filter.
      this.filters = {
        ...this.filters,
        [field]: { ...filter, constraints: [{ ...filter.constraints[0], value }] },
      };
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
      this.sortMeta = sortedColumns;

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
      if (this.dataType === "users" || this.dataType === "groups" || this.dataType === "tags") {
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
      if (this.isGrouped) this.updatePage(0);
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
        // Record every column that existed when this selection was saved, so that on
        // restore we can tell a genuinely new column apart from one the user deselected.
        knownColumns: this.availableColumns.map((col) => col.field),
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
            const savedVisible = customState.visibleColumns;
            const knownColumns = Array.isArray(customState.knownColumns)
              ? customState.knownColumns
              : null;

            // Whether the user previously had every *other* selectable column selected,
            // i.e. they had "select all". Legacy states (saved before knownColumns was
            // tracked) have no knownColumns, so we fall back to this check alone.
            const hadAllOthersSelected = (field) =>
              this.availableColumns
                .filter((col) => col.field !== field && !col.hidden)
                .every((col) => savedVisible.includes(col.field));

            this.selectedColumns = this.availableColumns.filter((col) => {
              // Keep whatever the user previously had selected.
              if (savedVisible.includes(col.field)) return true;
              // Never auto-show columns that are hidden by default.
              if (col.hidden) return false;
              // Otherwise the column wasn't in the saved selection: default it to visible
              // only if it is new since the selection was saved AND the user had selected
              // all other columns, so existing "select all" users keep seeing every column
              // while users who curated their columns keep their choices.
              const isNewColumn = knownColumns ? !knownColumns.includes(col.field) : true;
              return isNewColumn && hadAllOthersSelected(col.field);
            });

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

<style scoped>
.last-modified-cell {
  font-size: 0.85em;
  font-style: italic;
}
</style>
