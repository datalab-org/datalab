<template>
  <DynamicDataTable
    :columns="sampleColumns"
    :data="samples"
    :data-type="'samples'"
    :global-filter-fields="[
      'item_id',
      'name',
      'refcode',
      'chemform',
      'creatorsList',
      'blocks',
      'characteristic_chemical_formula',
    ]"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getSampleList } from "@/server_fetch_utils.js";

import FormattedItemName from "@/components/FormattedItemName";
import FormattedItemStatus from "@/components/FormattedItemStatus";
import ChemicalFormula from "@/components/ChemicalFormula";
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import BlocksIconCounter from "@/components/BlocksIconCounter";
import FilesIconCounter from "@/components/FilesIconCounter";
import FormattedCollectionName from "@/components/FormattedCollectionName";

import TextFilter from "@/components/TextFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";
import CreatorsAndGroupsFilter from "@/components/CreatorsAndGroupsFilter";
import DateRangeFilter from "@/components/DateRangeFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import {
  matchStatus,
  matchCollections,
  matchCreatorsAndGroups,
  matchBlocks,
  collectionsOptions,
  creatorsAndGroupsOptions,
  statusOptions,
  blocksOptions,
} from "@/utils/filterMatchers";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      sampleColumns: [
        {
          field: "item_id",
          header: "ID",
          label: "ID",
          body: {
            component: FormattedItemName,
            props: (row) => ({
              item_id: row.item_id,
              itemType: row.type !== undefined ? row.type : "samples",
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
          field: "type",
          header: "Type",
          label: "Type",
          filter: {
            component: MultiSelectFilter,
            componentProps: { optionLabel: "type", placeholder: "Select item types" },
            match: (value, filterValue) => {
              if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0))
                return true;
              if (Array.isArray(filterValue)) return filterValue.some((f) => f.type === value);
              return filterValue.type === value;
            },
            operator: FilterOperator.AND,
            options: (data) =>
              Array.from(new Set(data.map((item) => item.type))).map((type) => ({ type })),
            noOperator: true,
          },
        },
        {
          field: "status",
          header: "Status",
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
        { field: "name", header: "Name", label: "Sample name" },
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
          filter: {
            component: DateRangeFilter,
            matchMode: "dateRange",
            operator: FilterOperator.AND,
            noOperator: true,
          },
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
          field: "creatorsAndGroups",
          header: "Creators",
          label: "Creators",
          body: {
            component: Creators,
            props: (row) => ({
              creators: row.creatorsAndGroups
                ? row.creatorsAndGroups.filter((item) => item.type === "creator")
                : row.creators || [],
              groups: row.creatorsAndGroups
                ? row.creatorsAndGroups.filter((item) => item.type === "group")
                : row.groups || [],
              showNames:
                (row.creatorsAndGroups || row.creators || []).filter(
                  (item) => !item.type || item.type === "creator",
                ).length === 1,
              showBubble: true,
            }),
          },
          filter: {
            component: CreatorsAndGroupsFilter,
            match: matchCreatorsAndGroups,
            operator: FilterOperator.AND,
            options: creatorsAndGroupsOptions,
          },
        },
        {
          field: "blocks",
          header: "",
          icon: ["fa", "cubes"],
          label: "Blocks",
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
    samples() {
      if (!this.$store.state.sample_list) {
        return null;
      }
      return this.$store.state.sample_list.map((sample) => {
        return {
          ...sample,
          creatorsAndGroups: [
            ...(sample.creators || []).map((c) => ({ ...c, type: "creator" })),
            ...(sample.groups || []).map((g) => ({ ...g, type: "group" })),
          ],
          collectionsList: sample.collections
            .map((collection) => collection.collection_id)
            .join(", "),
          creatorsList: sample.creators.map((creator) => creator.display_name).join(", "),
        };
      });
    },
  },
  mounted() {
    this.getSamples();
  },
  methods: {
    getSamples() {
      getSampleList();
    },
  },
};
</script>
