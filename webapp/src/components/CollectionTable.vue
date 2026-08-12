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
import Creators from "@/components/Creators";

import TextFilter from "@/components/TextFilter";
import CreatorsAndGroupsFilter from "@/components/CreatorsAndGroupsFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";
import { matchCreatorsAndGroups, creatorsAndGroupsOptions } from "@/utils/filterMatchers";

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
        {
          field: "creatorsAndGroups",
          header: "Creators",
          label: "Creators",
          body: {
            component: Creators,
            props: (row) => ({
              creators: row.creatorsAndGroups
                ? row.creatorsAndGroups.filter((item) => item.type === "creator")
                : row.creators || [],
              groups: row.creatorsAndGroups
                ? row.creatorsAndGroups.filter((item) => item.type === "group")
                : row.groups || [],
              showNames:
                (row.creatorsAndGroups || row.creators || []).filter(
                  (item) => !item.type || item.type === "creator",
                ).length === 1,
              showBubble: true,
            }),
          },
          filter: {
            component: CreatorsAndGroupsFilter,
            match: matchCreatorsAndGroups,
            operator: FilterOperator.AND,
            options: creatorsAndGroupsOptions,
          },
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
