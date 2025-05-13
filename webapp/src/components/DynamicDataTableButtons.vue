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

    <div class="d-flex justify-content-between align-items-center">
      <div class="button-left">
        <button
          v-if="dataType === 'samples'"
          data-testid="add-item-button"
          class="btn btn-default me-2"
          @click="$emit('open-create-item-modal')"
        >
          Add an item
        </button>
        <button
          v-if="dataType === 'samples'"
          data-testid="batch-item-button"
          class="btn btn-default me-2"
          @click="$emit('open-batch-create-item-modal')"
        >
          Add batch of items
        </button>
        <button
          v-if="dataType === 'samples'"
          data-testid="scan-qr-button"
          class="btn btn-default me-2"
          aria-label="Scan QR code"
          title="Scan QR code"
          @click="$emit('open-qr-scanner-modal')"
        >
          <font-awesome-icon icon="qrcode" />
        </button>
        <button
          v-if="dataType === 'collections'"
          data-testid="add-collection-button"
          class="btn btn-default me-2"
          @click="$emit('open-create-collection-modal')"
        >
          Create new collection
        </button>
        <button
          v-if="dataType === 'startingMaterials' && editableInventory"
          data-testid="add-starting-material-button"
          class="btn btn-default me-2"
          @click="$emit('open-create-item-modal')"
        >
          Add a starting material
        </button>
        <button
          v-if="dataType === 'equipment'"
          data-testid="add-equipment-button"
          class="btn btn-default me-2"
          @click="$emit('open-create-equipment-modal')"
        >
          Add an item
        </button>
      </div>

      <div class="button-right d-flex">
        <MultiSelect
          :model-value="selectedColumns"
          :options="availableColumns"
          :option-label="columnLabel"
          placeholder="Select column(s) to display"
          display="chip"
          @update:model-value="$emit('update:selected-columns', $event)"
        >
          <template #value="{ value }">
            <span v-if="value && value.length == availableColumns.length" class="text-gray-400"
              >All columns displayed</span
            >
            <span v-else>{{ value.length }} columns displayed</span>
          </template>
        </MultiSelect>

        <IconField class="ms-2 d-flex align-items-center">
          <InputIcon>
            <font-awesome-icon icon="search" />
          </InputIcon>
          <InputText
            v-model="localFilters.global.value"
            data-testid="search-input"
            class="search-input form-control"
            placeholder="Search"
          />
        </IconField>

        <button
          data-testid="reset-table-button"
          class="btn btn-default ms-2"
          aria-label="Reset table"
          title="Reset table"
          @click="resetTable"
        >
          <font-awesome-icon icon="redo" />
        </button>
      </div>
    </div>

    <div v-if="itemsSelected.length > 0" class="d-flex justify-content-end align-items-center mt-2">
      <div class="dropdown">
        <button
          data-testid="selected-dropdown"
          class="btn btn-default dropdown-toggle"
          type="button"
          data-bs-toggle="dropdown"
          aria-expanded="false"
        >
          {{ itemsSelected.length }} selected...
        </button>
        <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
          <li v-if="dataType !== 'collections'">
            <a
              data-testid="add-to-collection-button"
              class="dropdown-item"
              href="#"
              @click.prevent="handleAddToCollection"
            >
              Add to collection
            </a>
          </li>
          <li>
            <a
              data-testid="delete-selected-button"
              class="dropdown-item"
              href="#"
              @click.prevent="confirmDeletion"
            >
              Delete selected
            </a>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="isColumnSelectModalOpen" class="modal d-block" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Select Columns</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="Close"
              @click="isColumnSelectModalOpen = false"
            ></button>
          </div>
          <div class="modal-body">
            <MultiSelect
              :model-value="selectedColumns"
              :options="availableColumns"
              :option-label="columnLabel"
              class="form-select"
              display="chip"
              @update:model-value="updateColumnsAndCloseModal"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import MultiSelect from "primevue/multiselect";
import "primeicons/primeicons.css";

import {
  deleteSample,
  deleteCollection,
  deleteStartingMaterial,
  deleteEquipment,
} from "@/server_fetch_utils.js";

export default {
  components: {
    IconField,
    InputIcon,
    InputText,
    MultiSelect,
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
  },
  emits: [
    "open-create-item-modal",
    "open-batch-create-item-modal",
    "open-qr-scanner-modal",
    "open-create-collection-modal",
    "open-create-equipment-modal",
    "open-add-to-collection-modal",
    "delete-selected-items",
    "update:filters",
    "update:selected-columns",
    "deletion-started",
    "deletion-completed",
    "deletion-error",
    "reset-table",
  ],
  data() {
    return {
      localFilters: { ...this.filters },
      isSelectedDropdownVisible: false,
      isDeletingItems: false,
      itemCount: 0,
      isColumnSelectModalOpen: false,
    };
  },
  watch: {
    itemsSelected(newVal) {
      if (newVal.length === 0) {
        this.isSelectedDropdownVisible = false;
      }
    },
    "localFilters.global.value"(newValue) {
      this.$emit("update:filters", { ...this.filters, global: { value: newValue } });
    },
  },
  methods: {
    confirmDeletion() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id || x.collection_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected items? (${idsSelected})`,
        )
      ) {
        this.deleteItems(idsSelected);
        this.$emit("delete-selected-items");
      }
      this.isSelectedDropdownVisible = false;
    },
    async deleteItems(ids) {
      try {
        this.itemCount = ids.length;
        this.isDeletingItems = true;
        this.$emit("deletion-started");

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

        this.$emit("deletion-completed");
      } catch (error) {
        console.error("Error during batch deletion:", error);
        this.$emit("deletion-error", error);
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
    resetTable() {
      if (
        window.confirm(
          "Are you sure you want to reset your preferences (visible columns, widths) for this table?",
        )
      ) {
        this.$emit("reset-table");
      }
    },
  },
};
</script>
