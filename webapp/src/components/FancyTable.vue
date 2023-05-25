<template>
  <Vue3EasyDataTable
    :headers="headers"
    :items="items"
    :search-value="searchValue"
    :loading="!isReady"
    :no-hover="true"
    :checkbox-column-width="40"
    :expand-column-width="40"
    table-class-name="customize-table"
    header-class-name="customize-table-header"
    buttons-pagination
    @click-row="goToEditPage"
    v-model:items-selected="itemsSelected"
  >
    <template #empty-message v-if="tableType == 'items'">No samples found.</template>
    <template #empty-message v-else>No collections found.</template>

    <template #expand="item" v-if="tableType == 'items'">
      <ItemDetails :item="item" />
    </template>

    <template #item-item_id="item" v-if="tableType == 'items'">
      <FormattedItemName
        :id="item.item_id"
        :item_id="item.item_id"
        :itemType="item?.type"
        enableModifiedClick
      />
    </template>

    <template #item-collection_id="item" v-if="tableType == 'collections'">
      <FormattedCollectionName
        :id="item.collection_id"
        :collection_id="item.collection_id"
        enableModifiedClick
      />
    </template>

    <template #item-creators="item">
      <Creators :creators="item.creators" :showNames="true" :showBubble="false" />
    </template>

    <template #item-chemform="item" v-if="tableType == 'items'">
      <ChemicalFormula :formula="item.chemform || item.characteristic_chemical_formula" />
    </template>

    <template #item-date="item" v-if="tableType == 'items'">
      {{ $filters.IsoDatetimeToDate(item.date) }}
    </template>

    <template #item-nblocks="item">
      <div style="text-align: right">
        {{ item.nblocks || 0 }}
      </div>
    </template>
  </Vue3EasyDataTable>
</template>

<script>
import Vue3EasyDataTable from "vue3-easy-data-table";
import "vue3-easy-data-table/dist/style.css";
import FormattedItemName from "@/components/FormattedItemName";
import FormattedCollectionName from "@/components/FormattedCollectionName";
import ChemicalFormula from "@/components/ChemicalFormula";
import ItemDetails from "@/components/ItemDetails";
import { GRAVATAR_STYLE, itemTypes } from "@/resources.js";
import Creators from "@/components/Creators";

export default {
  data() {
    return {
      gravatar_style: GRAVATAR_STYLE,
      itemTypes: itemTypes,
      itemsSelected: [],
    };
  },
  props: {
    items: Array,
    searchValue: String,
    isReady: Boolean,
    tableType: String,
  },
  computed: {
    headers() {
      if (this.tableType == "items") {
        return [
          { text: "ID", value: "item_id", sortable: true },
          { text: "Formula", value: "chemform", sortable: true },
          { text: "Date", value: "date", sortable: true },
          { text: "Creators", value: "creators", sortable: true },
          { text: "# of blocks", value: "nblocks", sortable: true },
        ];
      } else {
        return [
          { text: "ID", value: "collection_id", sortable: true },
          { text: "Date", value: "date", sortable: true },
          { text: "Creators", value: "creators", sortable: true },
          { text: "# of items", value: "num_items", sortable: true },
          { text: "# of blocks", value: "nblocks", sortable: true },
        ];
      }
    },
  },
  components: {
    ChemicalFormula,
    FormattedItemName,
    FormattedCollectionName,
    Vue3EasyDataTable,
    ItemDetails,
    Creators,
  },
  methods: {
    goToEditPage(row, event) {
      // don't actually go to editpage is this click is in the select column, because
      // that is easy to accidentally do. in future, could try to actuate the checkbox, too.
      if (event.target.querySelector(".easy-checkbox")) {
        return null;
      }
      // if using a modifier key (ctr, meta, alt), open in new tab
      // otherwise, go in this tab
      if (event.ctrl || event.metaKey || event.altKey) {
        window.open(`/edit/${row.item_id}`, "_blank");
      } else {
        if (this.tableType == "collections") {
          this.$router.push(`/collections/${row.collection_id}`);
        } else {
          this.$router.push(`/edit/${row.item_id}`);
        }
      }
    },
  },
};
</script>
<style>
.customize-table th {
  --easy-table-row-border: 2px solid #dee2e6;
  border-top: 0.5px solid #dee2e6 !important;
}

.customize-table tr {
  cursor: pointer;
}

.customize-table {
  --easy-table-border: none;
  --easy-table-row-border: 1px solid #dee2e6;
  --easy-table-header-font-size: 1rem;
  --easy-table-body-row-font-size: 1rem;
  --easy-table-footer-font-size: 1rem;
  --easy-table-message-font-size: 1rem;
}

.btn:disabled {
  cursor: not-allowed;
}
</style>
