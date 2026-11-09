<template>
  <DynamicDataTable
    :columns="tagColumns"
    :data="tags"
    data-type="tags"
    test-id="tags-table"
    :global-filter-fields="['name', 'description']"
    :show-buttons="true"
    @open-create-tag-modal="openCreateModal"
  />
  <TagFormModal
    v-model="tagModalIsOpen"
    :tag="editingTag"
    @tag-created="getTags"
    @tag-updated="getTags"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import TagFormModal from "@/components/TagFormModal.vue";
import { getTags } from "@/server_fetch_utils.js";

import TagActionsCell from "@/components/TagActionsCell";
import TagBadge from "@/components/TagBadge";
import TagScopeBadge from "@/components/TagScopeBadge";

import TextFilter from "@/components/TextFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";

export default {
  name: "TagManagementTable",
  components: { DynamicDataTable, TagFormModal },
  data() {
    return {
      tagModalIsOpen: false,
      editingTag: null,
      tagColumns: [
        {
          field: "name",
          header: "Tag",
          label: "Tag",
          body: {
            component: TagBadge,
            props: (row) => ({ tag: row }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by name" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "description",
          header: "Description",
          label: "Description",
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by description" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "scope",
          header: "Scope",
          label: "Scope",
          body: {
            component: TagScopeBadge,
            props: (row) => ({ tag: row }),
          },
        },
        {
          field: "actions",
          header: "Actions",
          sortable: false,
          body: {
            component: TagActionsCell,
            // `onEditTag` is bound as the cell's `edit-tag` listener, so the edit request
            // reaches this component without DynamicDataTable having to re-emit it.
            props: (row) => ({ tag: row, onEditTag: (tag) => this.openEditModal(tag) }),
          },
        },
      ],
    };
  },
  computed: {
    tags() {
      return this.$store.state.tag_list;
    },
  },
  created() {
    this.getTags();
  },
  methods: {
    getTags() {
      getTags();
    },
    openCreateModal() {
      this.editingTag = null;
      this.tagModalIsOpen = true;
    },
    openEditModal(tag) {
      this.editingTag = tag;
      this.tagModalIsOpen = true;
    },
  },
};
</script>
