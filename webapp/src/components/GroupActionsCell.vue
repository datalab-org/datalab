<template>
  <span class="mx-auto" style="text-align: center">
    <button
      class="btn btn-outline-success group-action-button mr-2"
      title="Edit group"
      @click="handleEdit"
    >
      Edit
    </button>
    <button
      class="btn btn-outline-danger group-action-button"
      title="Delete group"
      :disabled="isDeleting"
      @click="handleDelete"
    >
      <span v-if="isDeleting">Deleting...</span>
      <span v-else>Delete</span>
    </button>
  </span>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import { deleteGroup } from "@/server_fetch_utils.js";

export default {
  name: "GroupActionsCell",
  props: {
    group: {
      type: Object,
      required: true,
    },
    allGroups: {
      type: Array,
      required: true,
    },
  },
  emits: ["edit-group", "group-deleted"],
  data() {
    return {
      isDeleting: false,
    };
  },
  methods: {
    handleEdit() {
      this.$emit("edit-group", this.group);
    },
    async handleDelete() {
      const confirmed = await DialogService.confirm({
        title: "Delete Group",
        message: `Are you sure you want to delete the group "${this.group.display_name}"?<br><br>This action cannot be undone.`,
        type: "error",
        confirmButtonText: "Delete Group",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

      this.isDeleting = true;

      try {
        const groupId = this.group.immutable_id || this.group._id;
        await deleteGroup(groupId);

        this.$emit("group-deleted");
      } catch (error) {
        console.error("Error deleting group:", error);
        await DialogService.error({
          title: "Error",
          message: `Error deleting group: ${error.message}`,
        });
      } finally {
        this.isDeleting = false;
      }
    },
  },
};
</script>

<style scoped>
.group-action-button {
  font-family: var(--font-monospace);
  text-transform: uppercase;
  font-size: 0.8em;
  padding: 0.15rem 0.3rem;
  border: 2px solid;
}
</style>
