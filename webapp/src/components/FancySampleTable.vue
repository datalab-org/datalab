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

  <FancyTable
    :items="samples"
    :searchValue="searchValue"
    :isReady="isReady"
    :itemsSelected="itemsSelected"
    :tableType="tableType"
  />
</template>

<script>
import FancyTable from "@/components/FancyTable";
import CreateSampleModal from "@/components/CreateSampleModal";
import BatchCreateSampleModal from "@/components/BatchCreateSampleModal";
// eslint-disable-next-line no-unused-vars
import { getSampleList, deleteSample } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isFetchError: false,
      createSampleModalIsOpen: false,
      batchCreateSampleModalIsOpen: false,
      itemsSelected: [],
      isReady: false,
      tableType: "items",
      searchValue: "",
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list;
    },
  },
  methods: {
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
    FancyTable,
    CreateSampleModal,
    BatchCreateSampleModal,
  },
};
</script>
