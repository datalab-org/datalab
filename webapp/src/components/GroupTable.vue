<template>
  <DynamicDataTable
    :columns="groupColumns"
    :data="groups"
    data-type="groups"
    :global-filter-fields="['group_id', 'display_name', 'description']"
    :show-buttons="true"
    @groups-data-changed="getGroups"
    @edit-group="showEditModal"
    @group-deleted="onGroupDeleted"
  />
  <EditGroupModal
    :model-value="showEditGroupModal"
    :group="selectedGroup"
    @update:model-value="showEditGroupModal = $event"
    @group-updated="onGroupUpdated"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import EditGroupModal from "./EditGroupModal.vue";
import { getAdminGroupsList } from "@/server_fetch_utils.js";

import GroupIdCell from "@/components/GroupIdCell";
import GroupMembersCell from "@/components/GroupMembersCell";
import GroupActionsCell from "@/components/GroupActionsCell";

import TextFilter from "@/components/TextFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";

export default {
  name: "GroupTable",
  components: { DynamicDataTable, EditGroupModal },
  emits: ["group-updated"],
  data() {
    return {
      groupsList: null,
      selectedGroup: null,
      showEditGroupModal: false,
      groupColumns: [
        {
          field: "group_id",
          header: "Group ID",
          label: "Group ID",
          body: {
            component: GroupIdCell,
            props: (row) => ({ groupId: row.group_id }),
          },
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by group ID" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "display_name",
          header: "Name",
          label: "Name",
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
          field: "members",
          header: "# of members",
          label: "Members",
          body: {
            component: GroupMembersCell,
            props: (row) => ({ members: row.members }),
          },
        },
        {
          field: "actions",
          header: "Actions",
          sortable: false,
          body: {
            component: GroupActionsCell,
            props: (row) => ({ group: row.group, allGroups: row.allGroups }),
            events: ["edit-group", "group-deleted"],
          },
        },
      ],
    };
  },
  computed: {
    groups() {
      if (!this.groupsList) {
        return null;
      }
      return this.groupsList.map((group) => ({
        ...group,
        group: group,
        allGroups: this.groupsList,
      }));
    },
  },
  created() {
    this.getGroups();
  },
  methods: {
    async getGroups() {
      const data = await getAdminGroupsList();
      if (data != null) {
        this.groupsList = data;
      }
    },
    showEditModal(group) {
      this.selectedGroup = group;
      this.showEditGroupModal = true;
    },
    onGroupUpdated() {
      this.showEditGroupModal = false;
      this.getGroups();
      this.$emit("group-updated");
    },
    onGroupDeleted() {
      this.$emit("group-updated");
    },
  },
};
</script>
