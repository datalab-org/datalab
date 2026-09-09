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

import Creators from "@/components/Creators";

import { ITEM_ID_COLUMN, STATUS_COLUMN, NAME_COLUMN, DATE_COLUMN } from "@/utils/tableColumns";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      equipmentColumn: [
        {
          ...ITEM_ID_COLUMN,
          body: {
            ...ITEM_ID_COLUMN.body,
            props: (row) => ({
              ...ITEM_ID_COLUMN.body.props(row),
              itemType: row.type !== undefined ? row.type : "equipment",
            }),
          },
        },
        STATUS_COLUMN,
        NAME_COLUMN,
        DATE_COLUMN,
        { field: "location", header: "Location", label: "Location" },
        {
          field: "creators",
          header: "Maintainers",
          label: "Maintainers",
          body: {
            component: Creators,
            props: (row) => ({
              creators: row.creators || [],
              groups: [],
              showNames: (row.creators || []).length === 1,
              showBubble: true,
            }),
          },
        },
      ],
    };
  },
  computed: {
    equipment() {
      if (this.$store.state.equipment_list === null) {
        return null;
      }

      return this.$store.state.equipment_list;
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
