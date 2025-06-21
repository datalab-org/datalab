<template>
  <DynamicDataTable
    :columns="equipmentColumn"
    :data="equipment"
    :data-type="'equipment'"
    :global-filter-fields="['item_id', 'name', 'location', 'refcode']"
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
        { field: "item_id", header: "ID", body: "FormattedItemName", filter: true, label: "ID" },
        { field: "name", header: "Name", label: "Name" },
        { field: "date", header: "Date", label: "Date" },
        { field: "location", header: "Location", label: "Location" },
        { field: "creators", header: "Maintainers", body: "Creators", label: "Creators" },
      ],
    };
  },
  computed: {
    equipment() {
      if (this.$store.state.equipment_list === null) {
        return null;
      }

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
