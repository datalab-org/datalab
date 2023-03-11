<template>
  <div v-if="isSampleFetchError" class="alert alert-danger">
    Server Error. Sample list not retreived.
  </div>

  <div class="form-inline col-3 ml-auto mb-2">
    <div class="form-group">
      <label for="sample-table-search" class="sr-only">Hello</label>
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
    :items="samples"
    :search-value="searchValue"
    table-class-name="customize-table"
    header-class-name="customize-table-header"
    buttons-pagination
    @click-row="goToEditPage"
    v-model:items-selected="itemsSelected"
  >
    <template #item-date="item">
      {{ $filters.IsoDatetimeToDate(item.date) }}
    </template>

    <template #item-chemform="item">
      <ChemicalFormula :formula="item.chemform" />
    </template>

    <template #item-creators="item">
      <Creators :creators="item.creators" />
    </template>
  </Vue3EasyDataTable>
</template>

<script>
import Vue3EasyDataTable from "vue3-easy-data-table";
// import { Header, Item } from "vue3-easy-data-table"; // types
import "vue3-easy-data-table/dist/style.css";

import ChemicalFormula from "@/components/ChemicalFormula";
import Creators from "@/components/Creators";
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import crypto from "crypto";
import { GRAVATAR_STYLE } from "@/resources.js";

export default {
  data() {
    return {
      isSampleFetchError: false,
      gravatar_style: GRAVATAR_STYLE,
      sampleTableIsReady: false,
      itemsSelected: [],
      headers: [
        { text: "ID", value: "item_id", sortable: true },
        { text: "type", value: "type", sortable: true },
        { text: "Sample name", value: "name", sortable: true },
        { text: "Formula", value: "chemform", sortable: true },
        { text: "Date", value: "date", sortable: true },
        { text: "Creators", value: "creators" },
        { text: "# of blocks", value: "nblocks", sortable: true },
      ],
      searchValue: "",
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list;
    },
  },
  methods: {
    md5(value) {
      // Returns the MD5 hash of the given string.
      return crypto.createHash("md5").update(value).digest("hex");
    },
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
    getSamples() {
      getSampleList()
        .then(() => {
          console.log("sample list received!");
          this.sampleTableIsReady = true;
        })
        .catch(() => {
          this.isSampleFetchError = true;
        });
    },
    deleteSample(sample) {
      if (confirm(`Are you sure you want to delete sample "${sample.item_id}"?`)) {
        console.log("deleting...");
        deleteSample(sample.item_id, sample);
      }
      console.log("delete cancelled...");
    },
  },
  created() {
    this.getSamples();
  },
  components: {
    Vue3EasyDataTable,
    ChemicalFormula,
    Creators,
  },
};
</script>

<style scoped>
.avatar {
  border: 2px solid grey;
  border-radius: 50%;
}
.avatar:hover {
  border: 2px solid skyblue;
}
</style>

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
</style>
