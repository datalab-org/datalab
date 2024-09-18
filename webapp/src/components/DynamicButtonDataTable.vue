<template>
  <div class="button-group d-flex justify-content-between align-items-center">
    <div class="button-left">
      <button
        v-if="dataType === 'samples'"
        class="btn btn-default"
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
        class="btn btn-default"
        @click="$emit('open-create-collection-modal')"
      >
        Create new collection
      </button>
      <button
        v-if="dataType === 'startingMaterials' && editableInventory"
        class="btn btn-default"
        :disabled="itemsSelected.length === 0"
        @click="$emit('open-create-item-modal')"
      >
        Add a starting material
      </button>
      <button
        v-if="dataType === 'equipments'"
        class="btn btn-default"
        @click="$emit('open-create-equipment-modal')"
      >
        Add an item
      </button>
    </div>
    <div class="button-right d-flex">
      <button
        v-if="itemsSelected.length > 0 && dataType != 'collections'"
        class="btn btn-default"
        :disabled="itemsSelected.length === 0"
        @click="$emit('open-add-to-collection-modal')"
      >
        Add to collection
      </button>
      <button
        v-if="itemsSelected.length > 0"
        class="btn btn-default ml-2"
        data-testid="delete-selected-button"
        :disabled="itemsSelected.length === 0"
        @click="confirmDeletion"
      >
        Delete selected
      </button>

      <IconField>
        <InputIcon>
          <i class="pi pi-search"></i>
        </InputIcon>
        <InputText
          v-model="localFilters.global.value"
          data-testid="search-input"
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
    };
  },
  methods: {
    updateFilters() {
      this.$emit("update:filters", this.localFilters);
    },
    confirmDeletion() {
      if (this.dataType === "samples") {
        this.deleteSamples();
      } else if (this.dataType === "collections") {
        this.deleteCollections();
      } else if (this.dataType === "startingMaterials") {
        this.deleteStartingMaterials();
      } else if (this.dataType === "equipments") {
        this.deleteEquipments();
      }
      this.$emit("delete-selected-items");
    },
    deleteSamples() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected sample(s) (${idsSelected})?`,
        )
      ) {
        idsSelected.forEach((item_id) => {
          deleteSample(item_id);
        });
      }
    },
    deleteCollections() {
      const idsSelected = this.itemsSelected.map((x) => x.collection_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected collection(s) (${idsSelected})?`,
        )
      ) {
        idsSelected.forEach((collection_id) => {
          deleteCollection(collection_id, { collection_id: collection_id });
        });
      }
    },
    deleteStartingMaterials() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected starting material(s) (${idsSelected})?`,
        )
      ) {
        idsSelected.forEach((item_id) => {
          deleteStartingMaterial(item_id);
        });
      }
    },
    deleteEquipments() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected equipment(s) (${idsSelected})?`,
        )
      ) {
        idsSelected.forEach((item_id) => {
          deleteEquipment(item_id);
        });
      }
    },
  },
};
</script>
