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
          body: "FormattedItemName",
          bodyConfig: {
            item_id: "item_id",
            itemType: "item_type",
            enableClick: true,
          },
          label: "Item",
          filter: true,
        },
        {
          field: "active",
          header: "Token Status",
          body: "TokenStatusCell",
          label: "Status",
          filter: true,
        },
        {
          field: "refcode",
          header: "Refcode",
          body: "FormattedRefcode",
          bodyConfig: {
            refcode: "refcode",
            enableQRCode: true,
          },
          label: "Refcode",
          filter: true,
        },
        {
          field: "item_type",
          header: "Item Type",
          label: "Item Type",
          filter: true,
        },
        {
          field: "created_by_info",
          header: "Created By",
          body: "TokenCreatedByCell",
          bodyConfig: {
            creator: "created_by_info",
          },
          label: "Created By",
          filter: true,
        },
        {
          field: "created_at",
          header: "Date Created",
          label: "Date Created",
          filter: true,
        },
        {
          field: "actions",
          header: "Actions",
          body: "TokenActionsCell",
          bodyConfig: {
            token: "token",
            allTokens: "allTokens",
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
