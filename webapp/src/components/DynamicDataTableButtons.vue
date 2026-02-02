<template>
  <div v-if="showButtons" class="d-flex flex-column w-100">
    <div
      v-if="isDeletingItems"
      class="position-fixed d-flex justify-content-center align-items-center"
      style="background-color: rgba(255, 255, 255, 0.7); z-index: 1050; inset: 0"
    >
      <div class="card p-3 shadow-sm">
        <div class="text-center">
          <font-awesome-icon
            :icon="['fa', 'sync']"
            class="fa-2x text-primary mb-2"
            :spin="true"
            aria-label="loading"
          />
          <p class="mb-0 mt-1">Deleting {{ itemCount }} items...</p>
        </div>
      </div>
    </div>

    <div class="button-bar">
      <div v-if="dataType === 'samples'" class="btn-action-group">
        <button
          data-testid="add-item-button"
          class="btn btn-default btn-action"
          :title="adminSuperUserMode ? 'Disabled in super-user mode' : ''"
          @click="$emit('open-create-item-modal')"
        >
          Add an item
        </button>
        <button
          data-testid="batch-item-button"
          class="btn btn-default btn-action"
          :disabled="adminSuperUserMode"
          :title="adminSuperUserMode ? 'Disabled in super-user mode' : ''"
          @click="$emit('open-batch-create-item-modal')"
        >
          Add batch of items
        </button>
        <button
          data-testid="scan-qr-button"
          class="btn btn-default btn-action"
          aria-label="Scan QR code"
          title="Scan QR code"
          @click="$emit('open-qr-scanner-modal')"
        >
          <font-awesome-icon icon="qrcode" /> Scan QR code
        </button>
      </div>
      <button
        v-if="dataType === 'collections'"
        data-testid="add-collection-button"
        class="btn btn-default"
        @click="$emit('open-create-collection-modal')"
      >
        Create new collection
      </button>
      <button
        v-if="dataType === 'startingMaterials' && editableInventory"
        data-testid="add-starting-material-button"
        class="btn btn-default"
        @click="$emit('open-create-item-modal')"
      >
        Add a starting material
      </button>
      <button
        v-if="dataType === 'equipment'"
        data-testid="add-equipment-button"
        class="btn btn-default"
        @click="$emit('open-create-equipment-modal')"
      >
        Add an item
      </button>

      <div class="button-bar-spacer"></div>

      <div class="search-settings-group">
        <IconField class="search-field">
          <InputIcon>
            <font-awesome-icon icon="search" />
          </InputIcon>
          <InputText
            v-model="localFilters.global.value"
            data-testid="search-input"
            class="search-input"
            :placeholder="localUseApiSearch ? 'Search via API...' : 'Search'"
            :disabled="isLoadingApiSearch"
          />
        </IconField>

        <div class="btn-group ml-2" role="group" aria-label="Advanced search controls">
          <button
            data-testid="advanced-search-button"
            class="btn btn-default"
            aria-label="Advanced search"
            title="Advanced search via API"
            @click="openAdvancedSearchModal"
          >
            <font-awesome-icon icon="search-plus" />
          </button>

          <button
            v-if="useApiSearch"
            data-testid="clear-api-search-button"
            class="btn btn-default"
            aria-label="Clear API search"
            title="Clear API search and return to normal view"
            @click="clearApiSearch"
          >
            <font-awesome-icon icon="times" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="itemsSelected.length > 0" class="d-flex justify-content-end align-items-center mt-2">
      <div class="dropdown">
        <button
          data-testid="selected-dropdown"
          class="btn btn-default dropdown-toggle"
          type="button"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          @click="isSelectedDropdownVisible = !isSelectedDropdownVisible"
        >
          {{ itemsSelected.length }} selected...
        </button>
        <div
          v-show="isSelectedDropdownVisible"
          class="dropdown-menu"
          style="display: block"
          aria-labelledby="dropdownMenuButton"
        >
          <a
            v-if="dataType !== 'collections' && dataType !== 'collectionItems'"
            data-testid="add-to-collection-button"
            class="dropdown-item"
            @click="handleAddToCollection"
          >
            Add to collection
          </a>
          <a
            v-if="dataType === 'collectionItems'"
            data-testid="remove-from-collection-dropdown"
            class="dropdown-item"
            @click="confirmRemoveFromCollection"
          >
            Remove from collection
          </a>
          <a
            v-if="dataType !== 'collections' && dataType !== 'collectionItems'"
            data-testid="batch-share-button"
            class="dropdown-item"
            @click="handleBatchShare"
          >
            Batch share
          </a>
          <a
            v-if="dataType !== 'collectionItems'"
            data-testid="delete-selected-button"
            class="dropdown-item"
            @click="confirmDeletion"
          >
            Delete selected
          </a>
        </div>
      </div>
    </div>
  </div>
  <AdvancedSearchModal v-model="isAdvancedSearchModalVisible" @search="handleAdvancedSearch" />
</template>

<script>
import { DialogService } from "@/services/DialogService";

import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import MultiSelect from "primevue/multiselect";
import "primeicons/primeicons.css";

import AdvancedSearchModal from "@/components/AdvancedSearchModal";

import {
  deleteSample,
  deleteCollection,
  deleteStartingMaterial,
  deleteEquipment,
  removeItemsFromCollection,
} from "@/server_fetch_utils.js";

export default {
  components: {
    IconField,
    InputIcon,
    InputText,
    MultiSelect,
    AdvancedSearchModal,
  },
  props: {
    dataType: {
      type: String,
      required: true,
    },
    itemsSelected: {
      type: Array,
      required: true,
    },
    filters: {
      type: Object,
      required: true,
    },
    editableInventory: {
      type: Boolean,
      required: false,
      default: false,
    },
    // Global toggle for all buttons and search bar
    showButtons: {
      type: Boolean,
      required: false,
      default: true,
    },
    availableColumns: {
      type: Array,
      required: true,
    },
    selectedColumns: {
      type: Array,
      required: true,
    },
    collectionId: {
      type: String,
      required: false,
      default: null,
    },
    isLoadingApiSearch: {
      type: Boolean,
      required: false,
      default: false,
    },
    useApiSearch: { type: Boolean, default: false },
  },
  emits: [
    "open-create-item-modal",
    "open-batch-create-item-modal",
    "open-qr-scanner-modal",
    "open-create-collection-modal",
    "open-create-equipment-modal",
    "open-add-to-collection-modal",
    "open-batch-share-modal",
    "delete-selected-items",
    "update:filters",
    "update:selected-columns",
    "reset-table",
    "remove-selected-items-from-collection",
    "update:use-api-search",
    "api-search",
    "clear-api-search",
  ],
  data() {
    return {
      localFilters: { ...this.filters },
      isSelectedDropdownVisible: false,
      isSettingsDropdownVisible: false,
      isDeletingItems: false,
      itemCount: 0,
      isAdvancedSearchModalVisible: false,
    };
  },
  computed: {
    adminSuperUserMode() {
      return this.$store.getters.isAdminSuperUserModeActive;
    },
  },
  watch: {
    itemsSelected(newVal) {
      if (newVal.length === 0) {
        this.isSelectedDropdownVisible = false;
      }
    },
    localUseApiSearch(newValue) {
      this.$emit("update:use-api-search", newValue);
      if (!newValue) {
        this.localFilters.global.value = "";
      }
    },
    "localFilters.global.value"(newValue) {
      if (this.localUseApiSearch) {
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
          this.$emit("api-search", newValue);
        }, 1000);
      } else {
        this.$emit("update:filters", { ...this.filters, global: { value: newValue } });
      }
    },
  },
  beforeUnmount() {
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
    }
  },
  methods: {
    async confirmDeletion() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id || x.collection_id);
      let idsSelectedLabel = idsSelected;
      if (idsSelected.length > 10) {
        idsSelectedLabel = idsSelected.slice(0, 10).join(", ") + ", ...";
      }
      const confirmed = await DialogService.confirm({
        title: "Confirm Deletion",
        message: `Are you sure you want to delete ${this.itemsSelected.length} selected items? (${idsSelectedLabel})`,
        type: "warning",
      });
      if (confirmed) {
        this.deleteItems(idsSelected);
        this.$emit("delete-selected-items");
      }
      this.isSelectedDropdownVisible = false;
    },
    async deleteItems(ids) {
      try {
        this.itemCount = ids.length;
        this.isDeletingItems = true;

        let deletePromises = [];

        if (this.dataType === "samples") {
          deletePromises = ids.map((id) => deleteSample(id));
        } else if (this.dataType === "collections") {
          deletePromises = ids.map((id) => deleteCollection(id, { collection_id: id }));
        } else if (this.dataType === "startingMaterials") {
          deletePromises = ids.map((id) => deleteStartingMaterial(id));
        } else if (this.dataType === "equipment") {
          deletePromises = ids.map((id) => deleteEquipment(id));
        }

        await Promise.all(deletePromises);
      } catch (error) {
        console.error("Error during batch deletion:", error);
      } finally {
        this.isDeletingItems = false;
      }
    },
    async confirmRemoveFromCollection() {
      const refcodesSelected = this.itemsSelected.map((item) => item.refcode);

      if (
        confirm(
          `Are you sure you want to remove ${refcodesSelected.length} item(s) from ${this.collectionId} ? (${refcodesSelected})`,
        )
      ) {
        await this.removeItemsFromCollection(refcodesSelected);
        this.$emit("remove-selected-items-from-collection");
      }
      this.isSelectedDropdownVisible = false;
    },
    async removeItemsFromCollection(refcodes) {
      try {
        this.itemCount = refcodes.length;
        this.isDeletingItems = true;

        await removeItemsFromCollection(this.collectionId, refcodes);
      } catch (error) {
        console.error("Error during removal from collection:", error);
      } finally {
        this.isDeletingItems = false;
      }
    },
    handleAddToCollection() {
      this.$emit("open-add-to-collection-modal");
      this.isSelectedDropdownVisible = false;
    },
    columnLabel(option) {
      return option.label || option.header || option.field;
    },
    async resetTable() {
      this.isSettingsDropdownVisible = false;
      const confirmed = await DialogService.confirm({
        title: "Confirm reset",
        message:
          "Are you sure you want to reset your preferences (visible columns, widths) for this table?",
        type: "info",
      });
      if (confirmed) {
        this.$emit("reset-table");
      }
    },
    openAdvancedSearchModal() {
      this.isAdvancedSearchModalVisible = true;
    },
    handleAdvancedSearch(query) {
      this.$emit("api-search", query);
    },
    clearApiSearch() {
      this.$emit("clear-api-search");
    },
    handleBatchShare() {
      this.$emit("open-batch-share-modal");
      this.isSelectedDropdownVisible = false;
    },
  },
};
</script>

<style scoped>
.button-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.btn-action-group {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  flex: 1;
  text-align: center;
  white-space: nowrap;
}

.button-bar-spacer {
  flex: 1 1 auto;
  min-width: 0;
}

.search-settings-group {
  display: flex;
  gap: 0.5rem;
  flex: 0 1 auto;
  min-width: 0;
}

.search-field {
  flex: 1 1 80px;
  min-width: 80px;
  max-width: 200px;
}

.search-field :deep(.p-inputtext) {
  height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
}

.search-input {
  height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.25rem;
  width: 100%;
}

.settings-dropdown {
  min-width: 220px;
  padding: 0.5rem 0;
}

.dropdown-item-text {
  padding: 0.5rem 1rem;
}

.column-select-dropdown {
  width: 100%;
}
</style>
