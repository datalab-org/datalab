<template>
  <DynamicDataTable
    :columns="equipmentColumn"
    :data="equipment"
    :data-type="'equipment'"
    :global-filter-fields="['item_id', 'name', 'location', 'creatorsList']"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getEquipmentList } from "@/server_fetch_utils.js";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      equipmentColumn: [
        { field: "item_id", header: "ID", body: "FormattedItemName", filter: true },
        { field: "name", header: "Name" },
        { field: "date", header: "Date" },
        { field: "location", header: "Location" },
        { field: "creators", header: "Maintainers", body: "Creators" },
      ],
    };
  },
  computed: {
    equipment() {
      return this.$store.state.equipment_list.map((equipment) => ({
        ...equipment,
        // creatorsList: equipment.creators.map((creator) => creator.display_name).join(", "),
      }));
    },
  },
  mounted() {
    this.getEquipment();
  },
  methods: {
    getEquipment() {
      getEquipmentList();
    },
  },
};
</script>
