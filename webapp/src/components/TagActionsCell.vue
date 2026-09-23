<template>
  <span v-if="canManage" class="mx-auto" style="text-align: center">
    <button
      class="btn btn-outline-success tag-action-button mr-2"
      title="Edit tag"
      @click="$emit('edit-tag', tag)"
    >
      Edit
    </button>
    <button
      class="btn btn-outline-danger tag-action-button"
      title="Delete tag"
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
import { deleteTag } from "@/server_fetch_utils.js";

export default {
  name: "TagActionsCell",
  props: {
    tag: {
      type: Object,
      required: true,
    },
  },
  emits: ["edit-tag"],
  data() {
    return {
      isDeleting: false,
    };
  },
  computed: {
    // Global tags are managed by administrators; user-defined tags only
    // by their owner.
    canManage() {
      const isAdmin = this.$store.state.currentUserRole === "admin";
      if (this.tag.scope === "user") {
        return this.tag.owner === this.$store.state.currentUserID;
      }
      return isAdmin;
    },
  },
  methods: {
    async handleDelete() {
      const confirmed = await DialogService.confirm({
        title: "Delete Tag",
        message: `Are you sure you want to delete the tag "${this.tag.name}"?<br><br>It will be removed from any items using it. This action cannot be undone.`,
        type: "error",
        confirmButtonText: "Delete Tag",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

      this.isDeleting = true;
      try {
        // deleteTag updates the store (deleteFromTagList) on success, so the table refreshes.
        await deleteTag(this.tag.immutable_id);
      } catch (error) {
        console.error("Error deleting tag:", error);
      } finally {
        this.isDeleting = false;
      }
    },
  },
};
</script>

<style scoped>
/* Match the Groups management page action buttons (GroupActionsCell.vue). */
.tag-action-button {
  font-family: var(--font-monospace);
  text-transform: uppercase;
  font-size: 0.8em;
  padding: 0.15rem 0.3rem;
  border: 2px solid;
}
</style>
