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

import FormattedCollectionName from "@/components/FormattedCollectionName";
import TextFilter from "@/components/TextFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import { CREATORS_AND_GROUPS_COLUMN } from "@/utils/tableColumns";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      collectionColumn: [
        {
          field: "collection_id",
          header: "ID",
          label: "Collections",
          body: {
            component: FormattedCollectionName,
            props: (row) => ({
              collection_id: row.collection_id,
              enableClick: true,
              enableModifiedClick: true,
            }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by ID" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        { field: "title", header: "Title", label: "Title" },
        CREATORS_AND_GROUPS_COLUMN,
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
