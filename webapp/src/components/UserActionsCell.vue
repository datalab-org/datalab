<template>
  <span class="mx-auto" style="text-align: center">
    <button
      v-if="user.account_status === 'active'"
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
  </span>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import { saveUser } from "@/server_fetch_utils.js";

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
    async handleStatusChange(newStatus) {
      const originalStatus = this.user.account_status;

      const confirmed = await DialogService.confirm({
        title: "Change User Status",
        message: `Are you sure you want to change ${this.user.display_name}'s status from "${originalStatus}" to "${newStatus}"?`,
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
