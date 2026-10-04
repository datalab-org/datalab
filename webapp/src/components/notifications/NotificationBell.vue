<template>
  <div
    v-on-click-outside="close"
    class="notification-bell"
    data-testid="notification-bell"
    @keydown.esc="close"
  >
    <button
      class="btn border notification-bell-button"
      type="button"
      aria-label="Notifications"
      :aria-expanded="open"
      @click.stop="toggle"
    >
      <font-awesome-icon icon="bell" />
      <span v-if="unreadCount" class="notification-badge">{{ unreadLabel }}</span>
    </button>

    <div
      v-if="open"
      class="notification-popover"
      :class="{ 'has-detail': selectedNotification }"
      data-testid="notification-popover"
      @click.stop
    >
      <aside v-if="selectedNotification" class="notification-detail-pane">
        <div class="detail-pane-toolbar">
          <button
            class="btn btn-sm btn-outline-secondary mobile-back-button"
            type="button"
            aria-label="Back to notifications"
            @click="selectedNotification = null"
          >
            <font-awesome-icon icon="arrow-left" />
          </button>
          <button
            class="btn btn-sm btn-outline-secondary ml-auto"
            type="button"
            aria-label="Close notification details"
            @click="selectedNotification = null"
          >
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <NotificationDetail
          :notification="selectedNotification"
          @toggle-read="toggleRead"
          @toggle-archive="toggleArchive"
          @delete="confirmDelete"
        />
      </aside>

      <section class="notification-list-pane" :class="{ selected: selectedNotification }">
        <header class="notification-list-header">
          <strong>Notifications</strong>
          <button
            class="btn btn-sm btn-link mark-all-button"
            type="button"
            :disabled="unreadCount === 0"
            @click="markAllRead"
          >
            <font-awesome-icon icon="check" class="mr-1" />
            Mark all read
          </button>
        </header>

        <label class="show-archived-control">
          <input v-model="showArchived" type="checkbox" @change="refreshNotifications" />
          Show archived
        </label>

        <div v-if="loading" class="notification-state">
          <font-awesome-icon icon="spinner" spin class="mr-1" />
          Loading notifications
        </div>
        <div v-else-if="errorMessage" class="notification-state text-danger">
          <span>{{ errorMessage }}</span>
          <button class="btn btn-link p-0" type="button" @click="refreshNotifications">
            Retry
          </button>
        </div>
        <div v-else-if="notifications.length === 0" class="notification-state text-muted">
          No notifications
        </div>
        <div v-else class="notification-list">
          <article
            v-for="notification in notifications"
            :key="notification.immutable_id"
            class="notification-list-item"
            :class="{
              unread: !notification.read_at && !notification.archived_at,
              selected: selectedNotification?.immutable_id === notification.immutable_id,
            }"
            @click="openNotification(notification)"
          >
            <span class="notification-level" :class="`level-${notification.level}`"></span>
            <div class="notification-list-content">
              <strong>{{ notification.title }}</strong>
              <p v-if="summaryFor(notification)">{{ summaryFor(notification) }}</p>
              <small>
                <span v-if="notification.occurrence_count > 1">
                  {{ notification.occurrence_count }} occurrences &middot;
                </span>
                {{ formatDate(notification.last_occurred_at || notification.created_at) }}
              </small>
            </div>
            <button
              class="btn notification-read-button"
              type="button"
              :title="notification.read_at ? 'Mark unread' : 'Mark read'"
              :aria-label="
                notification.read_at ? 'Mark notification unread' : 'Mark notification read'
              "
              @click.stop="toggleRead(notification)"
            >
              <font-awesome-icon :icon="notification.read_at ? 'envelope' : 'envelope-open'" />
            </button>
          </article>
        </div>

        <footer class="notification-list-footer">
          <router-link to="/notifications" @click="close">View all notifications</router-link>
        </footer>
      </section>
    </div>
  </div>
</template>

<script>
import { vOnClickOutside } from "@vueuse/components";

import NotificationDetail from "@/components/notifications/NotificationDetail.vue";
import {
  formatNotificationDate,
  notificationSummary,
} from "@/components/notifications/notificationUtils.js";
import { DialogService } from "@/services/DialogService.js";
import {
  deleteNotification,
  getNotificationUnreadCount,
  getNotifications,
  markAllNotificationsRead,
  updateNotification,
} from "@/server_fetch_utils.js";

export default {
  name: "NotificationBell",
  directives: { onClickOutside: vOnClickOutside },
  components: { NotificationDetail },
  data() {
    return {
      open: false,
      notifications: [],
      unreadCount: 0,
      selectedNotification: null,
      showArchived: false,
      loading: false,
      errorMessage: "",
      refreshInterval: null,
    };
  },
  computed: {
    unreadLabel() {
      return this.unreadCount > 99 ? "99+" : String(this.unreadCount);
    },
  },
  mounted() {
    this.refreshUnreadCount();
    this.refreshInterval = window.setInterval(this.refreshUnreadCount, 120000);
  },
  beforeUnmount() {
    window.clearInterval(this.refreshInterval);
  },
  methods: {
    formatDate: formatNotificationDate,
    summaryFor: notificationSummary,
    async refreshUnreadCount() {
      try {
        const response = await getNotificationUnreadCount();
        this.unreadCount = response.unread_count;
      } catch (error) {
        console.warn("Unable to refresh notification count", error);
      }
    },
    async refreshNotifications() {
      this.loading = true;
      this.errorMessage = "";
      const selectedId = this.selectedNotification?.immutable_id;
      try {
        const response = await getNotifications({
          includeArchived: this.showArchived,
          limit: 20,
        });
        this.notifications = response.data;
        this.unreadCount = response.unread_count;
        this.selectedNotification = selectedId
          ? this.notifications.find((notification) => notification.immutable_id === selectedId) ||
            null
          : null;
      } catch (error) {
        this.errorMessage = "Unable to load notifications.";
      } finally {
        this.loading = false;
      }
    },
    async toggle() {
      this.open = !this.open;
      if (this.open) await this.refreshNotifications();
      else this.selectedNotification = null;
    },
    close() {
      this.open = false;
      this.selectedNotification = null;
    },
    async openNotification(notification) {
      this.selectedNotification = notification;
      if (!notification.read_at) {
        await this.updateNotificationState(notification, { read: true });
      }
    },
    async toggleRead(notification) {
      await this.updateNotificationState(notification, { read: notification.read_at == null });
    },
    async toggleArchive(notification) {
      const archived = notification.archived_at == null;
      await this.updateNotificationState(notification, { archived });
      if (archived && !this.showArchived) this.selectedNotification = null;
    },
    async updateNotificationState(notification, payload) {
      try {
        const response = await updateNotification(notification.immutable_id, payload);
        this.unreadCount = response.unread_count;
        this.selectedNotification = response.data;
        await this.refreshNotifications();
      } catch (error) {
        DialogService.error({
          title: "Unable to update notification",
          message: String(error),
        });
      }
    },
    async markAllRead() {
      try {
        const response = await markAllNotificationsRead();
        this.unreadCount = response.unread_count;
        await this.refreshNotifications();
      } catch (error) {
        DialogService.error({ title: "Unable to mark notifications read", message: String(error) });
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
        const response = await deleteNotification(notification.immutable_id);
        this.unreadCount = response.unread_count;
        this.selectedNotification = null;
        await this.refreshNotifications();
      } catch (error) {
        DialogService.error({ title: "Unable to delete notification", message: String(error) });
      }
    },
  },
};
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.notification-bell-button {
  position: relative;
  width: 2.6rem;
  height: 2.4rem;
  padding: 0;
}

.notification-badge {
  position: absolute;
  top: -0.45rem;
  right: -0.55rem;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.25rem;
  border: 2px solid #fff;
  border-radius: 0.7rem;
  background: #a51d2d;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1rem;
}

.notification-popover {
  --notification-list-width: 360px;
  position: absolute;
  top: calc(100% + 0.4rem);
  right: 0;
  z-index: 1050;
  display: grid;
  width: min(var(--notification-list-width), calc(100vw - 2rem));
  max-height: calc(100vh - 6rem);
  overflow: hidden;
  border: 1px solid #ced4da;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 0.5rem 1.25rem rgba(33, 37, 41, 0.18);
}

.notification-popover.has-detail {
  grid-template-columns: minmax(340px, 1.15fr) minmax(320px, 0.85fr);
  width: min(820px, calc(100vw - 2rem));
}

.notification-list-pane,
.notification-detail-pane {
  min-width: 0;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
}

.notification-detail-pane {
  padding: 0.85rem;
  border-right: 1px solid #dee2e6;
}

.detail-pane-toolbar {
  display: flex;
  margin-bottom: 0.5rem;
}

.mobile-back-button {
  display: none;
}

.notification-list-header,
.notification-list-footer {
  position: sticky;
  z-index: 2;
  display: flex;
  align-items: center;
  background: #fff;
}

.notification-list-header {
  top: 0;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.mark-all-button {
  font-size: 0.8rem;
}

.show-archived-control {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  margin: 0;
  padding: 0.45rem 0.75rem;
  border-bottom: 1px solid #edf0f2;
  color: #495057;
  font-size: 0.8rem;
}

.notification-state {
  display: grid;
  min-height: 8rem;
  padding: 1rem;
  place-content: center;
  gap: 0.35rem;
  text-align: center;
}

.notification-list-item {
  display: grid;
  grid-template-columns: 0.6rem minmax(0, 1fr) 2rem;
  gap: 0.45rem;
  align-items: start;
  padding: 0.7rem 0.75rem;
  border-bottom: 1px solid #edf0f2;
  cursor: pointer;
}

.notification-list-item.unread {
  background: #eef7fc;
}

.notification-list-item.selected {
  box-shadow: inset 3px 0 0 #2672a3;
}

.notification-list-content {
  min-width: 0;
}

.notification-list-content strong,
.notification-list-content p {
  overflow-wrap: anywhere;
}

.notification-list-content p {
  display: -webkit-box;
  margin: 0.25rem 0;
  overflow: hidden;
  color: #343a40;
  font-size: 0.85rem;
  white-space: pre-wrap;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.notification-list-content small {
  color: #6c757d;
}

.notification-level {
  width: 0.5rem;
  height: 0.5rem;
  margin-top: 0.35rem;
  border-radius: 50%;
  background: #2672a3;
}

.level-low {
  background: #6c757d;
}

.level-important {
  background: #a46800;
}

.level-urgent {
  background: #c2410c;
}

.level-critical {
  background: #a51d2d;
}

.notification-read-button {
  width: 2rem;
  height: 2rem;
  padding: 0;
  color: #495057;
}

.notification-list-footer {
  bottom: 0;
  justify-content: center;
  padding: 0.6rem;
  border-top: 1px solid #dee2e6;
  font-size: 0.85rem;
}

@media (max-width: 720px) {
  .notification-popover,
  .notification-popover.has-detail {
    position: fixed;
    top: 0.75rem;
    right: 0.75rem;
    bottom: 0.75rem;
    left: 0.75rem;
    display: block;
    width: auto;
    max-height: none;
  }

  .notification-list-pane,
  .notification-detail-pane {
    height: 100%;
    max-height: none;
  }

  .notification-list-pane.selected {
    display: none;
  }

  .notification-detail-pane {
    border-right: 0;
  }

  .mobile-back-button {
    display: inline-block;
  }
}
</style>
