<template>
  <Vue3EasyDataTable
    :headers="headers"
    :items="items"
    :search-value="searchValue"
    :loading="!isReady"
    table-class-name="customize-table"
    header-class-name="customize-table-header"
    buttons-pagination
    @click-row="goToEditPage"
    v-model:items-selected="itemsSelected"
  >
    <template #empty-message>No samples found.</template>

    <template #item-item_id="item">
      <FormattedItemName
        :id="item.item_id"
        :item_id="item.item_id"
        :itemType="item?.type"
        enableModifiedClick
      />
    </template>

    <template #item-type="item">
      {{ itemTypes[item.type].display }}
    </template>

    <template #item-chemform="item">
      <ChemicalFormula :formula="item.chemform || item.characteristic_chemical_formula" />
    </template>

    <template #item-date="item">
      {{ $filters.IsoDatetimeToDate(item.date) }}
    </template>

    <template #item-collections="item">
      <CollectionList :collections="item.collections" />
    </template>

    <template #item-creators="item">
      <div style="text-align: center">
        <Creators :creators="item.creators" />
      </div>
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
import CollectionList from "@/components/CollectionList";
import ChemicalFormula from "@/components/ChemicalFormula";
import Creators from "@/components/Creators";
import { GRAVATAR_STYLE, itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      gravatar_style: GRAVATAR_STYLE,
      itemTypes: itemTypes,
      itemsSelected: [],
    };
  },
  props: {
    headers: Array,
    items: Array,
    searchValue: String,
    isReady: Boolean,
  },
  components: {
    Creators,
    ChemicalFormula,
    FormattedItemName,
    Vue3EasyDataTable,
    CollectionList,
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
        this.$router.push(`/edit/${row.item_id}`);
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
