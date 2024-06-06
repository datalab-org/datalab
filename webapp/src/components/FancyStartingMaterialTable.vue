<template>
  <div v-if="isFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Server error: inventory could not be
    retrieved.
  </div>
  <div class="form-inline ml-auto col-3 mb-2">
    <div class="form-group">
      <label for="sample-table-search" class="sr-only">Search items</label>
      <input
        id="sample-table-search"
        type="text"
        class="form-control"
        v-model="searchValue"
        placeholder="search"
      />
    </div>
  </div>

  <Vue3EasyDataTable
    :headers="headers"
    :items="startingMaterials"
    :search-value="searchValue"
    table-class-name="customize-table"
    header-class-name="customize-table-header"
    buttons-pagination
    @click-row="goToEditPage"
  >
    <template #item-item_id="item">
      <FormattedItemName
        :item_id="item.item_id"
        :itemType="item?.type || 'starting_materials'"
        enableModifiedClick
      />
    </template>
    <template #item-chemform="item">
      <ChemicalFormula :formula="item.chemform" />
    </template>

    <template #item-date="item">
      {{ $filters.IsoDatetimeToDate(item.date) }}
    </template>
  </Vue3EasyDataTable>
</template>

<script>
import Vue3EasyDataTable from "vue3-easy-data-table";
import "vue3-easy-data-table/dist/style.css";

import ChemicalFormula from "@/components/ChemicalFormula";
import FormattedItemName from "@/components/FormattedItemName";
import { getStartingMaterialList } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isFetchError: false,
      searchValue: "",
      headers: [
        { text: "ID", value: "item_id", sortable: true },
        { text: "Name", value: "name", sortable: true },
        { text: "Formula", value: "chemform", sortable: true },
        { text: "Date Acquired", value: "date", sortable: true },
        { text: "# of blocks", value: "nblocks", sortable: true },
      ],
    };
  },
  computed: {
    startingMaterials() {
      return this.$store.state.starting_material_list;
    },
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
    getStartingMaterials() {
      getStartingMaterialList().catch(() => {
        this.isFetchError = true;
      });
    },
  },
  created() {
    this.getStartingMaterials();
  },
  components: {
    ChemicalFormula,
    FormattedItemName,
    Vue3EasyDataTable,
  },
};
</script>

<style scoped>
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
</style>
