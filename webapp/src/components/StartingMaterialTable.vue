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

export default {
  components: { DynamicDataTable },
  data() {
    return {
      startingMaterialColumn: [
        { field: "item_id", header: "ID", body: "FormattedItemName", filter: true, label: "ID" },
        {
          field: "barcode",
          body: "FormattedBarcode",
          header: "",
          label: "Barcode",
          icon: ["fa", "barcode"],
        },
        { field: "name", header: "Name", label: "Name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula", label: "Formula" },
        { field: "date", header: "Date", label: "Date" },
        { field: "location", header: "Location", label: "Location", filter: true },
        {
          field: "blocks",
          header: "",
          body: "BlocksIconCounter",
          icon: ["fa", "cubes"],
          label: "Block",
          filter: true,
        },
        {
          field: "nfiles",
          header: "",
          body: "FilesIconCounter",
          icon: ["fa", "file"],
          label: "Files",
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
