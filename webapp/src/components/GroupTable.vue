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
          body: "GroupIdCell",
          bodyConfig: {
            groupId: "group_id",
          },
          label: "Group ID",
          filter: true,
        },
        {
          field: "display_name",
          header: "Name",
          label: "Name",
          filter: true,
        },
        {
          field: "description",
          header: "Description",
          label: "Description",
          filter: true,
        },
        {
          field: "members",
          header: "# of members",
          body: "GroupMembersCell",
          bodyConfig: {
            members: "members",
          },
          label: "Members",
        },
        {
          field: "actions",
          header: "Actions",
          body: "GroupActionsCell",
          bodyConfig: {
            group: "group",
            allGroups: "allGroups",
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
