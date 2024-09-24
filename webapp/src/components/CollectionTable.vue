<template>
  <DynamicDataTable
    :columns="collectionColumn"
    :data="collections"
    :data-type="'collections'"
    :global-filter-fields="['collection_id', 'title', 'creatorsList']"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getCollectionList } from "@/server_fetch_utils.js";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      collectionColumn: [
        { field: "collection_id", header: "ID", body: "FormattedCollectionName", filter: true },
        { field: "title", header: "Title" },
        { field: "creators", header: "Creators", body: "Creators" },
      ],
    };
  },
  computed: {
    collections() {
      return this.$store.state.collection_list.map((sample) => ({
        ...sample,
        creatorsList: sample.creators.map((creator) => creator.display_name).join(", "),
      }));
    },
  },
  created() {
    this.getCollections();
  },
  methods: {
    getCollections() {
      getCollectionList();
    },
  },
};
</script>
