<template>
  <table class="table table-hover table-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">Group ID</th>
        <th scope="col">Name</th>
        <th scope="col">Description</th>
        <th scope="col">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="group in groups" :key="group.group_id">
        <td align="left">
          <span class="badge badge-light table-group-id">{{ group.group_id }}</span>
        </td>
        <td align="left">{{ group.display_name }}</td>
        <td align="left">{{ group.description }}</td>
        <td align="left">
          <button
            class="btn btn-outline-success btn-sm text-uppercase text-monospace mr-2"
            title="Edit group"
            @click="showEditModal(group)"
          >
            Edit
          </button>
          <button
            class="btn btn-outline-danger btn-sm text-uppercase text-monospace"
            title="Delete group"
            @click="confirmDeleteGroup(group)"
          >
            Delete
          </button>
        </td>
      </tr>
    </tbody>
  </table>
  <EditGroupModal
    :model-value="showEditGroupModal"
    :group="selectedGroup"
    @update:model-value="showEditGroupModal = $event"
    @group-updated="onGroupUpdated"
  />
</template>

<script>
import { getGroupsList, deleteGroup } from "@/server_fetch_utils.js";
import EditGroupModal from "./EditGroupModal.vue";

export default {
  components: {
    EditGroupModal,
  },
  emits: ["group-updated"],
  data() {
    return {
      groups: null,
      original_groups: null,
      selectedGroup: null,
      showEditGroupModal: false,
    };
  },
  created() {
    this.getGroups();
  },
  methods: {
    async getGroups() {
      let data = await getGroupsList();
      if (data != null) {
        this.groups = JSON.parse(JSON.stringify(data));
        this.original_groups = JSON.parse(JSON.stringify(data));
      }
    },

    async confirmDeleteGroup(group) {
      console.log("Group object:", group);

      if (
        window.confirm(
          `Are you sure you want to delete the group "${group.display_name}"? This action cannot be undone.`,
        )
      ) {
        try {
          const groupId = group.immutable_id || group._id;
          await deleteGroup({ immutable_id: groupId });
          await this.getGroups();
          this.$emit("group-updated");
        } catch (error) {
          console.error("Error deleting group:", error);
          alert("Error deleting group: " + error);
        }
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
  },
};
</script>

<style scoped>
td {
  vertical-align: middle;
}

.table-group-id {
  border: 2px solid #ccc;
}

select {
  border: 1px solid #ccc;
  border-radius: 0.25rem;
}

.badge {
  margin-left: 1em;
  font-family: "Andalé Mono", monospace;
}
</style>
