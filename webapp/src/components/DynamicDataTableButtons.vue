<template>
  <div v-if="showButtons" class="button-group d-flex justify-content-between align-items-center">
    <div class="button-left">
      <button
        v-if="dataType === 'samples'"
        class="btn btn-default ml-2"
        @click="$emit('open-create-item-modal')"
      >
        Add an item
      </button>
      <button
        v-if="dataType === 'samples'"
        class="btn btn-default ml-2"
        @click="$emit('open-batch-create-item-modal')"
      >
        Add batch of items
      </button>
      <button
        v-if="dataType === 'samples'"
        class="btn btn-default ml-2"
        @click="$emit('open-qr-scanner-modal')"
      >
        <font-awesome-icon icon="qrcode" /> Scan QR
      </button>
      <button
        v-if="dataType === 'collections'"
        class="btn btn-default ml-2"
        @click="$emit('open-create-collection-modal')"
      >
        Create new collection
      </button>
      <button
        v-if="dataType === 'startingMaterials' && editableInventory"
        class="btn btn-default ml-2"
        @click="$emit('open-create-item-modal')"
      >
        Add a starting material
      </button>
      <button
        v-if="dataType === 'equipment'"
        class="btn btn-default ml-2"
        @click="$emit('open-create-equipment-modal')"
      >
        Add an item
      </button>
    </div>
    <div class="button-right d-flex">
      <div class="dropdown">
        <button
          data-testid="selected-dropdown"
          class="btn btn-default dropdown-toggle"
          type="button"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          :disabled="itemsSelected.length === 0"
          @click="isSelectedDropdownVisible = !isSelectedDropdownVisible"
        >
          {{ itemsSelected.length > 0 ? `${itemsSelected.length} selected... ` : "Selected... " }}
        </button>
        <div
          v-show="isSelectedDropdownVisible"
          class="dropdown-menu"
          style="display: block"
          aria-labelledby="dropdownMenuButton"
        >
          <a
            v-if="itemsSelected.length !== 0 && dataType !== 'collections'"
            data-testid="add-to-collection-button"
            class="dropdown-item"
            @click="handleAddToCollection"
          >
            Add to collection
          </a>
          <a
            v-if="itemsSelected.length !== 0"
            data-testid="delete-selected-button"
            class="dropdown-item"
            @click="confirmDeletion"
          >
            Delete selected
          </a>
        </div>
      </div>

      <IconField>
        <InputIcon>
          <i class="pi pi-search"></i>
        </InputIcon>
        <InputText
          v-model="localFilters.global.value"
          data-testid="search-input"
          class="search-input"
          placeholder="Search"
          @input="updateFilters"
        />
      </IconField>
    </div>
  </div>
</template>

<script>
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
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
  ],
  data() {
    return {
      localFilters: { ...this.filters },
      isSelectedDropdownVisible: false,
    };
  },
  watch: {
    itemsSelected(newVal) {
      if (newVal.length === 0) {
        this.isSelectedDropdownVisible = false;
      }
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
    deleteItems(ids) {
      if (this.dataType === "samples") {
        ids.forEach((id) => deleteSample(id));
      } else if (this.dataType === "collections") {
        ids.forEach((id) => deleteCollection(id, { collection_id: id }));
      } else if (this.dataType === "startingMaterials") {
        ids.forEach((id) => deleteStartingMaterial(id));
      } else if (this.dataType === "equipment") {
        ids.forEach((id) => deleteEquipment(id));
      }
    },
    handleAddToCollection() {
      this.$emit("open-add-to-collection-modal");
      this.isSelectedDropdownVisible = false;
    },
  },
};
</script>

<style scoped>
.search-input {
  height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.25rem;
}

.button-right {
  gap: 0.5em;
}
</style>
