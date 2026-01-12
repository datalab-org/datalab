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
          :collection-id="collectionId"
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

      <!-- <Column expander style="width: 5rem" /> -->
      <Column
        v-for="column in selectedColumns"
        :key="column.field"
        :field="column.field"
        sortable
        :class="{ 'filter-active': isFilterActive(column.field) }"
        :style="{ minWidth: getColumnMinWidth(column) }"
        :filter-menu-class="
          column.field === 'type' || column.field === 'status' || column.field === 'date'
            ? 'no-operator'
            : ''
        "
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
        <template v-if="column.filter && column.field === 'creatorsAndGroups'" #filter>
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="uniqueCreatorsAndGroups"
            option-label="display_name"
            placeholder="Any"
            class="d-flex w-full"
            :filter="true"
            @click.stop
          >
            <template #option="slotProps">
              <div class="flex items-center">
                <UserBubble
                  v-if="slotProps.option.type === 'creator'"
                  :creator="slotProps.option"
                  :size="24"
                />
                <FormattedGroupName
                  v-if="slotProps.option.type === 'group'"
                  :group="slotProps.option"
                  :size="24"
                />
                <span v-if="slotProps.option.type === 'creator'" class="ml-1">{{
                  slotProps.option.display_name
                }}</span>
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
                    <UserBubble v-if="option.type === 'creator'" :creator="option" :size="20" />
                    <FormattedGroupName v-if="option.type === 'group'" :group="option" :size="20" />
                    <span v-if="option.type === 'creator'" class="ml-1">{{
                      option.display_name
                    }}</span>
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

        <template v-else-if="column.filter && column.field === 'status'" #filter="">
          <MultiSelect
            v-model="filters[column.field].constraints[0].value"
            :options="uniqueStatus"
            option-label="status"
            placeholder="Select status"
            class="d-flex w-full"
            :filter="true"
            @click.stop
          >
            <template #option="slotProps">
              <div class="flex items-center">
                <FormattedItemStatus :status="slotProps.option.status" :dot-only="false" />
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
                    <FormattedItemStatus :status="option.status" :dot-only="false" />
                  </span>
                </template>
                <span v-else class="text-gray-400">Any</span>
              </div>
            </template>
          </MultiSelect>
        </template>

        <template v-else-if="column.filter && column.field === 'date'" #filter="{ filterModel }">
          <div style="display: flex; flex-direction: column; gap: 0.5rem" @click.stop>
            <Select
              v-model="dateFilterMode"
              :options="dateFilterOptions"
              option-label="label"
              option-value="value"
              placeholder="Select filter type"
              class="w-full"
              @change="handleDateFilterModeChange(column.field)"
            />

            <DatePicker
              v-if="dateFilterMode === 'range'"
              v-model="filterModel.value"
              selection-mode="range"
              date-format="yy-mm-dd"
              placeholder="Select date range"
              :show-button-bar="true"
              :manual-input="false"
              :hide-on-range-selection="true"
              style="width: 100%"
            />

            <DatePicker
              v-else
              v-model="filterModel.value"
              date-format="yy-mm-dd"
              :placeholder="dateFilterMode === 'before' ? 'Before date' : 'After date'"
              :show-button-bar="true"
              :manual-input="false"
              style="width: 100%"
            />
          </div>
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

import FormattedItemName from "@/components/FormattedItemName";
import BlocksIconCounter from "@/components/BlocksIconCounter";
import FilesIconCounter from "@/components/FilesIconCounter";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import UserBubble from "@/components/UserBubble.vue";
import FormattedItemStatus from "@/components/FormattedItemStatus.vue";
import FormattedBarcode from "@/components/FormattedBarcode.vue";
import FormattedRefcode from "@/components/FormattedRefcode.vue";
import FormattedGroupName from "./FormattedGroupName.vue";
import GroupsIconCounter from "@/components/GroupsIconCounter";

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";
import DataTable from "primevue/datatable";
import MultiSelect from "primevue/multiselect";
import Column from "primevue/column";
import InputText from "primevue/inputtext";
import DatePicker from "primevue/datepicker";
import Select from "primevue/select";

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
    BatchShareModal,
    DataTable,
    MultiSelect,
    Column,
    InputText,
    FormattedItemName,
    FormattedCollectionName,
    FormattedItemStatus,
    FormattedGroupName,
    ChemicalFormula,
    CollectionList,
    Creators,
    UserBubble,
    GroupsIconCounter,
    DatePicker,
    Select,
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
  },
  emits: ["remove-selected-items-from-collection"],
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
        creatorsAndGroups: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "exactCreatorAndGroupMatch" }],
        },
        blocks: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "exactBlockMatch" }],
        },
        status: {
          operator: FilterOperator.OR,
          constraints: [{ value: null, matchMode: "exactStatusMatch" }],
        },
        date: {
          operator: FilterOperator.AND,
          constraints: [{ value: null, matchMode: "dateRange" }],
        },
      },
      filteredData: [],
      allowedTypes: INVENTORY_TABLE_TYPES,
      selectedColumns: [],
      dateFilterMode: "range",
      dateFilterOptions: [
        { label: "Date range", value: "range" },
        { label: "Created before", value: "before" },
        { label: "Created after", value: "after" },
      ],
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
    uniqueGroups() {
      if (!this.data) return [];
      const allGroups = this.data.flatMap((item) => item.groups || []);
      const uniqueGroupsMap = new Map();
      allGroups.forEach((group) => {
        if (group && group.group_id) {
          uniqueGroupsMap.set(group.group_id, { ...group });
        }
      });
      return Array.from(uniqueGroupsMap.values());
    },
    uniqueCreatorsAndGroups() {
      const hasVirtualField = this.data && this.data[0] && this.data[0].creatorsAndGroups;

      if (hasVirtualField) {
        const allItems = this.data.flatMap((item) => item.creatorsAndGroups || []);
        const uniqueMap = new Map();
        allItems.forEach((item) => {
          const key = `${item.type}-${item.display_name}`;
          if (!uniqueMap.has(key)) {
            uniqueMap.set(key, { ...item });
          }
        });
        return Array.from(uniqueMap.values());
      } else {
        const creators = this.uniqueCreators.map((c) => ({ ...c, type: "creator" }));
        return creators;
      }
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
    uniqueStatus() {
      return Array.from(
        new Set(this.data.filter((item) => item.status).map((item) => item.status)),
      ).map((status) => ({ status }));
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
    this.$store.commit("setPage", { type: this.dataType, page: 0 });

    const savedState = localStorage.getItem(`datatable-state-${this.dataType}`);
    if (savedState) {
      const parsed = JSON.parse(savedState);
      parsed.first = 0;
      localStorage.setItem(`datatable-state-${this.dataType}`, JSON.stringify(parsed));
    }
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

      const currentItem = this.data.find((item) => {
        if (item.creatorsAndGroups) {
          return JSON.stringify(item.creators) === JSON.stringify(value);
        } else {
          return JSON.stringify(item.creators) === JSON.stringify(value);
        }
      });

      if (!currentItem) return false;

      const itemsToFilter =
        currentItem.creatorsAndGroups ||
        (currentItem.creators || []).map((c) => ({ ...c, type: "creator" }));

      if (Array.isArray(filterValue)) {
        if (isAnd) {
          return filterValue.every((filter) =>
            itemsToFilter.some(
              (item) => item.display_name === filter.display_name && item.type === filter.type,
            ),
          );
        } else {
          return filterValue.some((filter) =>
            itemsToFilter.some(
              (item) => item.display_name === filter.display_name && item.type === filter.type,
            ),
          );
        }
      }

      return itemsToFilter.some(
        (item) => item.display_name === filterValue.display_name && item.type === filterValue.type,
      );
    });
    FilterService.register("exactCreatorAndGroupMatch", (value, filterValue) => {
      if (!filterValue || !value) return true;

      const filter = this.filters.creatorsAndGroups;
      const isAnd = filter.operator === FilterOperator.AND;

      if (Array.isArray(filterValue)) {
        if (isAnd) {
          return filterValue.every((filter) =>
            value.some(
              (item) => item.display_name === filter.display_name && item.type === filter.type,
            ),
          );
        } else {
          return filterValue.some((filter) =>
            value.some(
              (item) => item.display_name === filter.display_name && item.type === filter.type,
            ),
          );
        }
      }

      return value.some(
        (item) => item.display_name === filterValue.display_name && item.type === filterValue.type,
      );
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

    FilterService.register("exactStatusMatch", (value, filterValue) => {
      if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0)) {
        return true;
      }

      if (Array.isArray(filterValue)) {
        return filterValue.some((f) => f.status === value);
      }

      return filterValue.status === value;
    });

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
  },
  methods: {
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
    updateFilter(field, value) {
      this.$nextTick(() => {
        this.filters[field].constraints[0].value = value;
      });
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

      const clickedElement = event.originalEvent.target;
      const isFormattedCollectionName = clickedElement.closest(" .formatted-collection-name");
      if (isFormattedCollectionName && isFormattedCollectionName.classList.contains("clickable")) {
        return null;
      }

      if (window.Cypress) {
        window.location.href = `/${this.editPageRoutePrefix}/${row_id}`;
      } else {
        if (event.originalEvent.ctrlKey || event.originalEvent.metaKey) {
          window.open(`/${this.editPageRoutePrefix}/${row_id}`, "_blank");
        } else {
          window.location.href = `/${this.editPageRoutePrefix}/${row_id}`;
        }
      }
    },
    getComponentProps(componentName, data) {
      const propsConfig = {
        FormattedItemName: {
          item_id: "item_id",
          itemType: "type",
          enableClick: true,
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
          enableClick: true,
          enableModifiedClick: true,
        },
        ChemicalFormula: {
          formula: "chemform",
        },
        CollectionList: {
          collections: "collections",
        },
        Creators: {
          creators: data.creators || [],
          groups: data.groups || [],
          showNames: data.creators?.length === 1,
        },
        FormattedItemStatus: {
          status: "status",
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

      if (componentName === "Creators") {
        props.creators = data.creators || [];
        props.groups = data.groups || [];
      }

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
    handleResetTable() {
      localStorage.removeItem(`datatable-state-${this.dataType}`);

      this.$nextTick(() => {
        location.reload();
      });
    },
    handleDateFilterModeChange(field) {
      this.filters[field].constraints[0].value = null;

      if (this.dateFilterMode === "range") {
        this.filters[field].constraints[0].matchMode = "dateRange";
      } else if (this.dateFilterMode === "before") {
        this.filters[field].constraints[0].matchMode = "dateBefore";
      } else if (this.dateFilterMode === "after") {
        this.filters[field].constraints[0].matchMode = "dateAfter";
      }
    },
    onDateRangeSelect(value) {
      if (
        this.dateFilterMode === "range" &&
        Array.isArray(value) &&
        value.length === 2 &&
        value[1] !== null
      ) {
        return;
      }
    },
  },
};
</script>
