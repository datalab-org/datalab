<template>
  <DynamicDataTable
    :columns="startingMaterialColumn"
    :data="startingMaterials"
    :data-type="'startingMaterials'"
    :global-filter-fields="['item_id', 'name', 'chemform', 'chemical_purity', 'nblocks']"
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
        { field: "item_id", header: "ID", body: "FormattedItemName", filter: true },
        { field: "name", header: "Name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula" },
        { field: "date", header: "Date" },
        { field: "chemical_purity", header: "Purity" },
        { field: "nblocks", header: "", body: "BaseIconCounter" },
        { field: "nfiles", header: "", body: "FilesIconCounter" },
      ],
    };
  },
  computed: {
    startingMaterials() {
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
