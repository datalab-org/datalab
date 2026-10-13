<template>
  <span class="mx-auto" style="text-align: center">
    <span v-if="user.account_status === 'deleted'" class="text-muted">&mdash;</span>
    <button
      v-else-if="user.account_status === 'active'"
      class="btn btn-outline-danger status-action-button"
      @click="handleStatusChange('deactivated')"
    >
      Deactivate
    </button>
    <button
      v-else
      class="btn btn-outline-success status-action-button"
      @click="handleStatusChange('active')"
    >
      Activate
    </button>
    <button
      v-if="user.account_status !== 'deleted'"
      class="btn btn-outline-danger status-action-button ml-1"
      @click="handleDelete"
    >
      Delete
    </button>
  </span>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import { saveUser, deleteUser } from "@/server_fetch_utils.js";

export default {
  name: "UserActionsCell",
  props: {
    user: {
      type: Object,
      required: true,
    },
    allUsers: {
      type: Array,
      required: true,
    },
  },
  methods: {
    async handleDelete() {
      // Unverified accounts have never been able to create any content, so they can be
      // removed from the database entirely; all others are tombstoned
      const expunge = this.user.account_status === "unverified";
      const name = this.user.display_name;

      const message = expunge
        ? `<p><strong>This is destructive and cannot be undone.</strong></p>
           <p>The unverified account <strong>${name}</strong> will be removed from the database entirely.</p>`
        : `<p><strong>This is destructive and cannot be undone.</strong></p>
           <p>All personal data for <strong>${name}</strong> will be removed, including their connected accounts, email addresses and API keys.
           Their display name will be replaced with a random pseudonym, and the account can never be used to log in again.</p>
           <p>Anything they created (items, collections, files) will be kept and remain attributed to the pseudonymous account.
           If you only want to prevent them from logging in temporarily, deactivate the account instead.</p>`;

      const confirmed = await DialogService.confirm({
        title: "Delete user account",
        message:
          message +
          `<p class="mb-0 text-muted">Note: the removed data will likely persist in database backups for some time, in case a restore is needed.</p>`,
        type: "warning",
        confirmButtonText: "Delete account",
      });

      if (!confirmed) return;

      try {
        const response = await deleteUser(this.user.immutable_id, expunge);
        const userInArray = this.allUsers.find((u) => u.immutable_id === this.user.immutable_id);
        if (userInArray) {
          userInArray.account_status = "deleted";
          if (!expunge) {
            userInArray.display_name = response.display_name;
          }
        }
      } catch (err) {
        DialogService.error({
          title: "Error",
          message: `Failed to delete user: ${err}`,
        });
      }
    },
    async handleStatusChange(newStatus) {
      const originalStatus = this.user.account_status;

      const confirmed = await DialogService.confirm({
        title: "Change User Status",
        message: `Are you sure you want to change <strong>${this.user.display_name}'s</strong> status from "${originalStatus}" to "${newStatus}"?`,
        type: "warning",
      });

      if (confirmed) {
        try {
          await saveUser(this.user.immutable_id, { account_status: newStatus });

          const userInArray = this.allUsers.find((u) => u.immutable_id === this.user.immutable_id);
          if (userInArray) {
            userInArray.account_status = newStatus;
          }
        } catch (err) {
          DialogService.error({
            title: "Error",
            message: "Failed to update user status.",
          });
        }
      }
    },
  },
};
</script>

<style scoped>
.status-action-button {
  font-family: var(--font-monospace);
  text-transform: uppercase;
  font-size: 0.8em;
  padding: 0.15rem 0.3rem;
  border: 2px solid;
}
</style>
