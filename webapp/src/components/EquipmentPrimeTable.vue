<template>
  <PrimeTable
    :columns="equipmentColumn"
    :data="equipments"
    :data-type="'equipments'"
    :global-filter-fields="['item_id', 'name', 'location', 'creatorsList']"
  />
</template>

<script>
import PrimeTable from "@/components/PrimeTable";
import { getEquipmentList } from "@/server_fetch_utils.js";

export default {
  components: { PrimeTable },
  data() {
    return {
      equipmentColumn: [
        { field: "item_id", header: "ID", body: "FormattedItemName", filter: true },
        { field: "name", header: "Name", filter: true },
        { field: "date", header: "Date" },
        { field: "location", header: "Location" },
        { field: "creators", header: "Maintainers", body: "Creators" },
      ],
    };
  },
  computed: {
    equipments() {
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
