<template>
  <DynamicDataTable
    :columns="collectionColumn"
    :data="collections"
    :data-type="'collections'"
    :global-filter-fields="['collection_id', 'title']"
    :edit-page-route-prefix="'collections'"
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
        {
          field: "collection_id",
          header: "ID",
          body: "FormattedCollectionName",
          filter: true,
          label: "Collections",
        },
        { field: "title", header: "Title", label: "Title" },
        {
          field: "creatorsAndGroups",
          header: "Creators",
          body: "Creators",
          filter: true,
          label: "Creators",
        },
      ],
    };
  },
  computed: {
    collections() {
      if (this.$store.state.collection_list === null) {
        return null;
      }

      return this.$store.state.collection_list.map((collection) => ({
        ...collection,
        creatorsAndGroups: [...(collection.creators || []).map((c) => ({ ...c, type: "creator" }))],
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
