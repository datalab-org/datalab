<template>
  <DynamicDataTable
    :columns="tokenColumns"
    :data="tokens"
    data-type="tokens"
    :global-filter-fields="['item_id', 'refcode', 'item_type']"
    :show-buttons="true"
    @tokens-data-changed="loadTokens"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { API_URL } from "@/resources.js";

import FormattedItemName from "@/components/FormattedItemName";
import FormattedRefcode from "@/components/FormattedRefcode";
import TokenStatusCell from "@/components/TokenStatusCell";
import TokenActionsCell from "@/components/TokenActionsCell";
import TokenCreatedByCell from "@/components/TokenCreatedByCell";
import UserBubble from "@/components/UserBubble";

import MultiSelectFilter from "@/components/MultiSelectFilter";
import SingleSelectFilter from "@/components/SingleSelectFilter";
import DateRangeFilter from "@/components/DateRangeFilter";
import TextFilter from "@/components/TextFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";

export default {
  name: "TokenTable",
  components: { DynamicDataTable },
  data() {
    return {
      tokensList: null,
      tokenColumns: [
        {
          field: "item_id",
          header: "Item",
          label: "Item",
          body: {
            component: FormattedItemName,
            props: (row) => ({
              item_id: row.item_id,
              itemType: row.item_type,
              enableClick: true,
            }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by item" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "active",
          header: "Token Status",
          label: "Status",
          body: {
            component: TokenStatusCell,
            props: (row) => ({ active: row.active }),
          },
          filter: {
            component: SingleSelectFilter,
            componentProps: {
              optionValue: "active",
              placeholder: "Any",
              showClear: true,
              optionComponent: TokenStatusCell,
              optionProps: (opt) => ({ active: opt.active }),
              valueComponent: TokenStatusCell,
              valueProps: (val) => ({ active: val }),
            },
            match: (value, filterValue) => {
              if (filterValue === null || filterValue === undefined) return true;
              return value === filterValue;
            },
            operator: FilterOperator.OR,
            options: () => [
              { active: true, label: "Active" },
              { active: false, label: "Invalidated" },
            ],
          },
        },
        {
          field: "refcode",
          header: "Refcode",
          label: "Refcode",
          body: {
            component: FormattedRefcode,
            props: (row) => ({ refcode: row.refcode, enableQRCode: true }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by refcode" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "item_type",
          header: "Item Type",
          label: "Item Type",
          filter: {
            component: MultiSelectFilter,
            componentProps: {
              optionLabel: "item_type",
              placeholder: "Select item types",
            },
            match: (value, filterValue) => {
              if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0))
                return true;
              if (Array.isArray(filterValue)) return filterValue.some((f) => f.item_type === value);
              return filterValue.item_type === value;
            },
            operator: FilterOperator.AND,
            options: (data) =>
              Array.from(new Set(data.map((token) => token.item_type).filter(Boolean))).map(
                (type) => ({ item_type: type }),
              ),
          },
        },
        {
          field: "created_by_info",
          header: "Created By",
          label: "Created By",
          body: {
            component: TokenCreatedByCell,
            props: (row) => ({ creator: row.created_by_info }),
          },
          filter: {
            component: MultiSelectFilter,
            componentProps: {
              optionLabel: "display_name",
              placeholder: "Any",
              optionComponent: UserBubble,
              optionProps: (opt) => ({ creator: opt, size: 24 }),
              valueComponent: UserBubble,
              valueProps: (val) => ({ creator: val, size: 20 }),
              showOptionLabel: true,
            },
            match: (value, filterValue) => {
              if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0))
                return true;
              if (!value) return false;
              if (Array.isArray(filterValue)) {
                return filterValue.some((f) => f.immutable_id === value.immutable_id);
              }
              return filterValue.immutable_id === value.immutable_id;
            },
            operator: FilterOperator.AND,
            options: (data) =>
              Array.from(
                new Map(
                  data
                    .map((token) => token.created_by_info)
                    .filter(Boolean)
                    .map((creator) => [creator.immutable_id, creator]),
                ).values(),
              ),
          },
        },
        {
          field: "created_at",
          header: "Date Created",
          label: "Date Created",
          getValue: (row) => (row.created_at ? row.created_at.substring(0, 10) : row.created_at),
          filter: {
            component: DateRangeFilter,
            matchMode: "dateRange",
            operator: FilterOperator.AND,
            noOperator: true,
          },
        },
        {
          field: "actions",
          header: "Actions",
          sortable: false,
          body: {
            component: TokenActionsCell,
            props: (row) => ({ token: row.token, allTokens: row.allTokens || [] }),
          },
        },
      ],
    };
  },
  computed: {
    tokens() {
      if (!this.tokensList) {
        return null;
      }
      return this.tokensList.map((token) => ({
        ...token,
        token: token,
        allTokens: this.tokensList,
      }));
    },
  },
  created() {
    this.loadTokens();
  },
  methods: {
    async loadTokens() {
      try {
        const response = await fetch(`${API_URL}/access-tokens`, {
          method: "GET",
          credentials: "include",
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          this.tokensList = data.tokens;
        } else {
          console.error("Failed to load tokens:", data.message);
        }
      } catch (error) {
        console.error("Error loading tokens:", error);
      }
    },
  },
};
</script>
