<template>
  <DynamicDataTable
    :columns="startingMaterialColumn"
    :data="startingMaterials"
    :data-type="'startingMaterials'"
    :global-filter-fields="[
      'item_id',
      'barcode',
      'refcode',
      'name',
      'chemform',
      'blocks',
      'supplier',
      'location',
    ]"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getStartingMaterialList } from "@/server_fetch_utils.js";

import FormattedItemName from "@/components/FormattedItemName";
import FormattedItemStatus from "@/components/FormattedItemStatus";
import FormattedBarcode from "@/components/FormattedBarcode";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import BlocksIconCounter from "@/components/BlocksIconCounter";
import FilesIconCounter from "@/components/FilesIconCounter";
import FormattedCollectionName from "@/components/FormattedCollectionName";

import TextFilter from "@/components/TextFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import {
  matchStatus,
  matchCollections,
  matchBlocks,
  matchStringValues,
  collectionsOptions,
  statusOptions,
  blocksOptions,
  stringValuesOptions,
} from "@/utils/filterMatchers";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      startingMaterialColumn: [
        {
          field: "item_id",
          header: "ID",
          label: "ID",
          body: {
            component: FormattedItemName,
            props: (row) => ({
              item_id: row.item_id,
              itemType: row.type !== undefined ? row.type : "starting_materials",
              enableClick: true,
              enableModifiedClick: true,
            }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by ID" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "status",
          header: "Status",
          label: "Status",
          body: {
            component: FormattedItemStatus,
            props: (row) => ({ status: row.status }),
          },
          filter: {
            component: MultiSelectFilter,
            componentProps: {
              optionLabel: "status",
              placeholder: "Select status",
              optionComponent: FormattedItemStatus,
              optionProps: (opt) => ({ status: opt.status, dotOnly: false }),
              valueComponent: FormattedItemStatus,
              valueProps: (val) => ({ status: val.status, dotOnly: false }),
            },
            match: matchStatus,
            operator: FilterOperator.OR,
            options: statusOptions,
            noOperator: true,
          },
        },
        {
          field: "barcode",
          header: "",
          label: "Barcode",
          icon: ["fa", "barcode"],
          body: {
            component: FormattedBarcode,
            props: (row) => ({
              barcode: row.barcode,
              enableBarcode: false,
              enableModifiedClick: false,
            }),
          },
        },
        { field: "name", header: "Name", label: "Name" },
        {
          field: "chemform",
          header: "Formula",
          label: "Formula",
          body: {
            component: ChemicalFormula,
            props: (row) => ({
              formula: row.chemform,
              smiles: row.smiles,
              inchiKey: row.inchi_key,
              ghsCodes: row.GHS_codes,
              molarMass: row.molar_mass,
              cas: row.CAS,
            }),
          },
        },
        {
          field: "date",
          header: "Date",
          label: "Date",
          getValue: (row) => (row.date ? row.date.substring(0, 10) : row.date),
        },
        {
          field: "collections",
          header: "Collections",
          label: "Collections",
          body: {
            component: CollectionList,
            props: (row) => ({ collections: row.collections }),
          },
          filter: {
            component: MultiSelectFilter,
            componentProps: {
              optionLabel: "collection_id",
              optionComponent: FormattedCollectionName,
              optionProps: (opt) => ({ collection_id: opt.collection_id, size: 24 }),
              valueComponent: FormattedCollectionName,
              valueProps: (val) => ({ collection_id: val.collection_id, size: 20 }),
            },
            match: matchCollections,
            operator: FilterOperator.AND,
            options: collectionsOptions,
          },
        },
        {
          field: "supplier",
          header: "Supplier",
          label: "Supplier",
          filter: {
            component: MultiSelectFilter,
            componentProps: { placeholder: "Any" },
            match: matchStringValues,
            operator: FilterOperator.AND,
            options: stringValuesOptions("supplier"),
          },
        },
        {
          field: "location",
          header: "Location",
          label: "Location",
          filter: {
            component: MultiSelectFilter,
            componentProps: { placeholder: "Any" },
            match: matchStringValues,
            operator: FilterOperator.AND,
            options: stringValuesOptions("location"),
          },
        },
        {
          field: "blocks",
          header: "",
          icon: ["fa", "cubes"],
          label: "Block",
          body: {
            component: BlocksIconCounter,
            props: (row) => ({ count: row.nblocks, blockInfo: row.blocks }),
          },
          filter: {
            component: MultiSelectFilter,
            componentProps: { optionLabel: "label", placeholder: "Select block types" },
            match: matchBlocks,
            operator: FilterOperator.AND,
            options: blocksOptions,
          },
        },
        {
          field: "nfiles",
          header: "",
          icon: ["fa", "file"],
          label: "Files",
          body: {
            component: FilesIconCounter,
            props: (row) => ({ count: row.nfiles }),
          },
        },
      ],
    };
  },
  computed: {
    startingMaterials() {
      if (this.$store.state.starting_material_list === null) {
        return null;
      }

      return this.$store.state.starting_material_list;
    },
  },
  mounted() {
    this.getStartingMaterials();
  },
  methods: {
    getStartingMaterials() {
      getStartingMaterialList();
    },
  },
};
</script>
