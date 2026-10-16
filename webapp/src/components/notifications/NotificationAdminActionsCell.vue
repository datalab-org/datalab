<template>
  <button
    class="btn btn-outline-danger notification-delete-button"
    type="button"
    title="Delete delivery"
    aria-label="Delete notification delivery"
    :disabled="deleting"
    @click.stop="deleteDelivery"
  >
    <font-awesome-icon :icon="deleting ? 'spinner' : 'trash'" :spin="deleting" />
  </button>
</template>

<script>
import { deleteAdminNotification } from "@/server_fetch_utils.js";
import { DialogService } from "@/services/DialogService";

export default {
  name: "NotificationAdminActionsCell",
  props: {
    notification: { type: Object, required: true },
  },
  emits: ["notification-deleted"],
  data() {
    return { deleting: false };
  },
  methods: {
    async deleteDelivery() {
      const recipient = this.notification.recipient_info?.display_name || "this recipient";
      const confirmed = await DialogService.confirm({
        title: "Delete notification delivery",
        message: `Permanently delete "${this.notification.title}" for ${recipient}?`,
        type: "warning",
        confirmButtonText: "Delete",
      });
      if (!confirmed) return;

      this.deleting = true;
      try {
        await deleteAdminNotification(this.notification.immutable_id);
        this.$emit("notification-deleted", this.notification);
      } catch (error) {
        DialogService.error({
          title: "Unable to delete notification",
          message: String(error),
        });
      } finally {
        this.deleting = false;
      }
    },
  },
};
</script>

<style scoped>
.notification-delete-button {
  width: 2rem;
  height: 2rem;
  padding: 0;
}
</style>
