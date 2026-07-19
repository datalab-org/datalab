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

import FormattedItemName from "@/components/FormattedItemName";
import FormattedItemStatus from "@/components/FormattedItemStatus";
import Creators from "@/components/Creators";

import TextFilter from "@/components/TextFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import { matchStatus, statusOptions } from "@/utils/filterMatchers";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      equipmentColumn: [
        {
          field: "item_id",
          header: "ID",
          body: {
            component: FormattedItemName,
            props: (row) => ({
              item_id: row.item_id,
              itemType: row.type !== undefined ? row.type : "equipment",
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
        { field: "name", header: "Name" },
        {
          field: "date",
          header: "Date",
          getValue: (row) => (row.date ? row.date.substring(0, 10) : row.date),
        },
        { field: "location", header: "Location" },
        {
          field: "creators",
          header: "Maintainers",
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
