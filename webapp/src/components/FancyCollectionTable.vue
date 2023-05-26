<template>
  <div v-if="isFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />
    &nbsp;Collection list could not be retreived. Are you logged in?
  </div>

  <FancyTable
    :items="collections"
    :searchValue="searchValue"
    :isReady="isReady"
    :itemsSelected="itemsSelected"
    :tableType="tableType"
  />
</template>

<script>
import FancyTable from "@/components/FancyTable";
// eslint-disable-next-line no-unused-vars
import { getCollectionList, deleteCollection } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isFetchError: false,
      createSampleModalIsOpen: false,
      batchCreateSampleModalIsOpen: false,
      itemsSelected: [],
      isReady: false,
      tableType: "collections",
      searchValue: "",
    };
  },
  computed: {
    collections() {
      return this.$store.state.collection_list;
    },
  },
  methods: {
    getCollections() {
      getCollectionList()
        .then(() => {
          this.isReady = true;
        })
        .catch(() => {
          this.isFetchError = true;
        });
    },
    deleteCollection(collection) {
      if (
        confirm(
          `Are you sure you want to delete collection "${collection.collection_id}"?\nThis will not delete any items.`
        )
      ) {
        deleteCollection(collection.collection_id, collection);
      }
    },
  },
  created() {
    this.getCollections();
  },
  components: {
    FancyTable,
  },
};
</script>
