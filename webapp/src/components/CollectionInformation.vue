<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <div id="collection-information">
          <div class="form-row">
            <div class="form-group col">
              <label for="name" class="mr">Title</label>
              <input
                id="name"
                v-model="Title"
                placeholder="Add a title"
                class="form-control"
                style="border: none"
              />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group col-md-6">
              <ToggleableCreatorsFormGroup
                v-model="CollectionCreators"
                :collection-id="collection_id"
              />
            </div>
            <div class="form-group col-md-6">
              <ToggleableGroupsFormGroup
                v-model="CollectionGroups"
                :collection-id="collection_id"
              />
            </div>
          </div>
        </div>

        <label id="description-label" class="mr-2">Description</label>
        <TiptapInline
          v-model="CollectionDescription"
          aria-labelledby="description-label"
        ></TiptapInline>
        <div class="form-row">
          <div class="form-group col">
            <ExportButton :collection-id="collection_id" />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <CollectionRelationshipVisualization :collection_id="collection_id" />
      </div>
    </div>
    <DynamicDataTable
      :data="children"
      :columns="collectionTableColumns"
      :data-type="'collectionItems'"
      :global-filter-fields="[
        'item_id',
        'status',
        'name',
        'refcode',
        'blocks',
        'chemform',
        'characteristic_chemical_formula',
      ]"
      :show-buttons="true"
      :collection-id="collection_id"
    />
  </div>
</template>

<script>
import { createComputedSetterForCollectionField } from "@/field_utils.js";
import TiptapInline from "@/components/TiptapInline";
import Creators from "@/components/Creators";
import CollectionRelationshipVisualization from "@/components/CollectionRelationshipVisualization";
import DynamicDataTable from "@/components/DynamicDataTable";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedItemStatus from "@/components/FormattedItemStatus.vue";
import ChemicalFormula from "@/components/ChemicalFormula";
import BlocksIconCounter from "@/components/BlocksIconCounter";
import FilesIconCounter from "@/components/FilesIconCounter";
import ExportButton from "@/components/ExportButton";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import ToggleableGroupsFormGroup from "@/components/ToggleableGroupsFormGroup";

import TextFilter from "@/components/TextFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import { matchStatus, statusOptions } from "@/utils/filterMatchers";

export default {
  components: {
    TiptapInline,
    CollectionRelationshipVisualization,
    DynamicDataTable,
    ExportButton,
    ToggleableCreatorsFormGroup,
    ToggleableGroupsFormGroup,
  },
  props: {
    collection_id: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      collectionTableColumns: [
        {
          field: "item_id",
          header: "ID",
          label: "ID",
          body: {
            component: FormattedItemName,
            props: (row) => ({
              item_id: row.item_id,
              itemType: row.type,
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
              Array.from(new Set(data.map((item) => item.type).filter(Boolean))).map((type) => ({
                type,
              })),
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
        { field: "name", header: "Sample name", label: "Sample Name" },
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
          field: "creators",
          header: "Creators",
          label: "Creators",
          body: {
            component: Creators,
            props: (row) => ({
              creators: row.creators || [],
              groups: row.groups || [],
              showNames: (row.creators || []).length === 1,
              showBubble: true,
            }),
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
    CollectionID: createComputedSetterForCollectionField("collection_id"),
    CollectionDescription: createComputedSetterForCollectionField("description"),
    Title: createComputedSetterForCollectionField("title"),
    Name: createComputedSetterForCollectionField("name"),
    CollectionCreators: createComputedSetterForCollectionField("creators"),
    CollectionGroups: createComputedSetterForCollectionField("groups"),
    children() {
      return this.$store.state.all_collection_children[this.collection_id] || [];
    },
    collectionRefcode() {
      const collection = this.$store.state.all_collection_data[this.collection_id];
      return collection?.refcode || null;
    },
  },
};
</script>
