<template>
  <div v-if="isFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Sample list could not be retreived. Are you
    logged in?
  </div>

  <div class="container mb-2 mx-0">
    <div class="row form-inline">
      <div class="col-md-6 px-0">
        <div class="d-flex justify-content-start">
          <button class="btn btn-default mr-2" @click="createSampleModalIsOpen = true">
            Add an item
          </button>
          <button class="btn btn-default mr-2" @click="batchCreateSampleModalIsOpen = true">
            Add batch of samples
          </button>
        </div>
      </div>
      <div class="col-md-6 px-0">
        <div class="d-flex justify-content-end">
          <button
            class="btn btn-default mr-2"
            :disabled="!Boolean(itemsSelected.length)"
            @click="deleteSelectedItems"
          >
            Delete selected
          </button>
          <div class="form-group">
            <label for="sample-table-search" class="sr-only">Search items</label>
            <input
              id="sample-table-search"
              type="text"
              class="form-control"
              v-model="searchValue"
              placeholder="Search..."
            />
          </div>
        </div>
      </div>
    </div>
  </div>

  <CreateSampleModal v-model="createSampleModalIsOpen" />
  <BatchCreateSampleModal v-model="batchCreateSampleModalIsOpen" />

  <Vue3EasyDataTable
    :headers="headers"
    :items="samples"
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
import CreateSampleModal from "@/components/CreateSampleModal";
import BatchCreateSampleModal from "@/components/BatchCreateSampleModal";
// eslint-disable-next-line no-unused-vars
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";
import { GRAVATAR_STYLE, itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      isFetchError: false,
      gravatar_style: GRAVATAR_STYLE,
      itemTypes: itemTypes,
      isReady: false,
      createSampleModalIsOpen: false,
      batchCreateSampleModalIsOpen: false,
      itemsSelected: [],
      headers: [
        { text: "ID", value: "item_id", sortable: true },
        { text: "type", value: "type", sortable: true },
        { text: "Sample name", value: "name", sortable: true },
        { text: "Formula", value: "chemform", sortable: true },
        { text: "Date", value: "date", sortable: true },
        { text: "Collections", value: "collections", sortable: true },
        { text: "Creators", value: "creators", sortable: true },
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
          this.isReady = true;
        })
        .catch(() => {
          this.isFetchError = true;
        });
    },
    deleteSelectedItems() {
      const idsSelected = this.itemsSelected.map((x) => x.item_id);
      if (
        confirm(
          `Are you sure you want to delete ${this.itemsSelected.length} selected items (${idsSelected})?`
        )
      ) {
        console.log("deleting...");
        idsSelected.forEach((item_id) => {
          console.log(`deleting item ${item_id}`);
          deleteSample(item_id);
        });
      } else {
        console.log("delete cancelled...");
      }
    },
  },
  created() {
    this.getSamples();
  },
  components: {
    Vue3EasyDataTable,
    ChemicalFormula,
    Creators,
    FormattedItemName,
    CollectionList,
    CreateSampleModal,
    BatchCreateSampleModal,
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

.btn:disabled {
  cursor: not-allowed;
}
</style>
