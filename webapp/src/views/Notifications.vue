<template>
  <Navbar />
  <main class="container notifications-page">
    <div class="notifications-heading">
      <div>
        <h1>Notifications</h1>
        <p class="text-muted mb-0">Notifications sent to your account.</p>
      </div>
      <button class="btn btn-outline-secondary" type="button" @click="loadNotifications">
        <font-awesome-icon icon="sync" :spin="loading" class="mr-1" />
        Refresh
      </button>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <NotificationTable :notifications="notifications" @row-click="openNotification" />

    <Modal v-model="detailOpen" :is-large="true">
      <template #header>Notification details</template>
      <template #body>
        <NotificationDetail
          v-if="selectedNotification"
          :notification="selectedNotification"
          @toggle-read="toggleRead"
          @toggle-archive="toggleArchive"
          @delete="confirmDelete"
        />
      </template>
      <template #footer>
        <button type="button" class="btn btn-secondary" @click="detailOpen = false">Close</button>
      </template>
    </Modal>
  </main>
</template>

<script>
import Modal from "@/components/Modal.vue";
import Navbar from "@/components/Navbar.vue";
import NotificationDetail from "@/components/notifications/NotificationDetail.vue";
import NotificationTable from "@/components/notifications/NotificationTable.vue";
import { DialogService } from "@/services/DialogService.js";
import { deleteNotification, getNotifications, updateNotification } from "@/server_fetch_utils.js";

export default {
  name: "NotificationsView",
  components: { Modal, Navbar, NotificationDetail, NotificationTable },
  data() {
    return {
      notifications: null,
      selectedNotification: null,
      detailOpen: false,
      loading: false,
      errorMessage: "",
    };
  },
  created() {
    this.loadNotifications();
  },
  methods: {
    async loadNotifications() {
      this.loading = true;
      this.errorMessage = "";
      try {
        const response = await getNotifications({ includeArchived: true, limit: 100 });
        this.notifications = response.data;
        if (this.selectedNotification) {
          this.selectedNotification =
            this.notifications.find(
              (notification) =>
                notification.immutable_id === this.selectedNotification.immutable_id,
            ) || null;
        }
      } catch (error) {
        this.notifications = [];
        this.errorMessage = `Unable to load notifications: ${String(error)}`;
      } finally {
        this.loading = false;
      }
    },
    async openNotification(notification) {
      this.selectedNotification = notification;
      this.detailOpen = true;
      if (!notification.read_at) {
        await this.updateSelected(notification, { read: true });
      }
    },
    async toggleRead(notification) {
      await this.updateSelected(notification, { read: notification.read_at == null });
    },
    async toggleArchive(notification) {
      await this.updateSelected(notification, { archived: notification.archived_at == null });
    },
    async updateSelected(notification, payload) {
      try {
        const response = await updateNotification(notification.immutable_id, payload);
        this.selectedNotification = response.data;
        await this.loadNotifications();
      } catch (error) {
        DialogService.error({
          title: "Unable to update notification",
          message: String(error),
        });
      }
    },
    async confirmDelete(notification) {
      const confirmed = await DialogService.confirm({
        title: "Delete notification",
        message: `Permanently delete "${notification.title}"?`,
        type: "warning",
        confirmButtonText: "Delete",
      });
      if (!confirmed) return;

      try {
        await deleteNotification(notification.immutable_id);
        this.detailOpen = false;
        this.selectedNotification = null;
        await this.loadNotifications();
      } catch (error) {
        DialogService.error({
          title: "Unable to delete notification",
          message: String(error),
        });
      }
    },
  },
};
</script>

<style scoped>
.notifications-page {
  padding-top: 1.5rem;
  padding-bottom: 2rem;
}

.notifications-heading {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.notifications-heading h1 {
  margin: 0;
  font-size: 1.6rem;
}

@media (max-width: 576px) {
  .notifications-heading {
    align-items: flex-start;
  }
}
</style>
