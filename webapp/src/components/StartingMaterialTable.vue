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

import FormattedBarcode from "@/components/FormattedBarcode";
import MultiSelectFilter from "@/components/MultiSelectFilter";

import { FilterOperator } from "@primevue/core/api";
import { matchStringValues, stringValuesOptions } from "@/utils/filterMatchers";
import {
  ITEM_ID_COLUMN,
  STATUS_COLUMN,
  NAME_COLUMN,
  CHEMFORM_COLUMN,
  DATE_COLUMN,
  COLLECTIONS_COLUMN,
  BLOCKS_COLUMN,
  FILES_COLUMN,
  LAST_MODIFIED_COLUMN,
} from "@/utils/tableColumns";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      startingMaterialColumn: [
        {
          ...ITEM_ID_COLUMN,
          body: {
            ...ITEM_ID_COLUMN.body,
            props: (row) => ({
              ...ITEM_ID_COLUMN.body.props(row),
              itemType: row.type !== undefined ? row.type : "starting_materials",
            }),
          },
        },
        STATUS_COLUMN,
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
        NAME_COLUMN,
        CHEMFORM_COLUMN,
        DATE_COLUMN,
        COLLECTIONS_COLUMN,
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
        { ...BLOCKS_COLUMN, label: "Block" },
        FILES_COLUMN,
        LAST_MODIFIED_COLUMN,
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
