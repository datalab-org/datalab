<template>
  <article class="notification-detail">
    <header class="notification-detail-header">
      <div class="notification-heading">
        <span class="notification-level" :class="`level-${notification.level}`"></span>
        <h3>{{ notification.title }}</h3>
      </div>
      <div v-if="showActions" class="notification-actions">
        <button
          class="btn btn-sm btn-outline-secondary"
          type="button"
          :title="isRead ? 'Mark unread' : 'Mark read'"
          @click="$emit('toggle-read', notification)"
        >
          <font-awesome-icon :icon="isRead ? 'envelope' : 'envelope-open'" />
          {{ isRead ? "Mark unread" : "Mark read" }}
        </button>
        <button
          class="btn btn-sm btn-outline-secondary"
          type="button"
          :title="isArchived ? 'Unarchive' : 'Archive'"
          @click="$emit('toggle-archive', notification)"
        >
          <font-awesome-icon :icon="isArchived ? 'undo' : 'archive'" />
          {{ isArchived ? "Unarchive" : "Archive" }}
        </button>
        <button
          class="btn btn-sm btn-outline-danger"
          type="button"
          title="Delete notification"
          @click="$emit('delete', notification)"
        >
          <font-awesome-icon icon="trash" />
          Delete
        </button>
      </div>
    </header>

    <div class="notification-meta">
      <span>{{ statusLabel }}</span>
      <span v-if="notification.occurrence_count > 1">
        {{ notification.occurrence_count }} occurrences
      </span>
      <span>{{ formatDate(notification.last_occurred_at || notification.created_at) }}</span>
    </div>

    <div v-if="hasOccurrences" class="notification-occurrences">
      <section
        v-for="(occurrence, index) in occurrences"
        :key="`${occurrence.occurred_at}-${index}`"
        class="notification-occurrence"
      >
        <div class="notification-occurrence-meta">
          <span class="notification-level" :class="`level-${occurrence.level}`"></span>
          <span>{{ formatDate(occurrence.occurred_at) }}</span>
          <span v-if="occurrence.is_new" class="new-occurrence">New</span>
        </div>
        <p v-if="occurrence.summary" class="notification-summary">{{ occurrence.summary }}</p>
        <p v-if="occurrence.message" class="notification-message">{{ occurrence.message }}</p>
      </section>
    </div>

    <template v-else>
      <p v-if="notification.summary" class="notification-summary">{{ notification.summary }}</p>
      <p v-if="notification.message" class="notification-message">{{ notification.message }}</p>
      <p v-if="!notification.summary && !notification.message" class="text-muted mb-0">
        No additional details.
      </p>
    </template>
  </article>
</template>

<script>
import {
  formatNotificationDate,
  notificationOccurrences,
  notificationStatus,
} from "@/components/notifications/notificationUtils.js";

export default {
  name: "NotificationDetail",
  props: {
    notification: { type: Object, required: true },
    showActions: { type: Boolean, default: true },
  },
  emits: ["toggle-read", "toggle-archive", "delete"],
  computed: {
    isRead() {
      return this.notification.read_at != null;
    },
    isArchived() {
      return this.notification.archived_at != null;
    },
    statusLabel() {
      const status = notificationStatus(this.notification);
      return status.charAt(0).toUpperCase() + status.slice(1);
    },
    occurrences() {
      return notificationOccurrences(this.notification);
    },
    hasOccurrences() {
      return this.notification.occurrence_count > 1 && this.occurrences.length > 0;
    },
  },
  methods: {
    formatDate: formatNotificationDate,
  },
};
</script>

<style scoped>
.notification-detail {
  min-width: 0;
  color: #212529;
}

.notification-detail-header {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.notification-heading {
  display: flex;
  min-width: 0;
  gap: 0.5rem;
  align-items: center;
}

.notification-heading h3 {
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 1.05rem;
  line-height: 1.3;
}

.notification-actions {
  display: flex;
  flex-wrap: wrap;
  flex-shrink: 0;
  gap: 0.35rem;
  justify-content: flex-end;
}

.notification-meta,
.notification-occurrence-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  color: #6c757d;
  font-size: 0.8rem;
}

.notification-meta {
  margin: 0.65rem 0;
}

.notification-meta span + span::before {
  margin-right: 0.5rem;
  content: "\00b7";
}

.notification-level {
  display: inline-block;
  width: 0.55rem;
  height: 0.55rem;
  flex: 0 0 0.55rem;
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

.notification-summary,
.notification-message {
  margin: 0.5rem 0 0;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.notification-summary {
  font-weight: 600;
}

.notification-occurrence {
  padding: 0.75rem 0;
  border-top: 1px solid #edf0f2;
}

.notification-occurrence:first-child {
  border-top: 0;
}

.new-occurrence {
  padding: 0.05rem 0.3rem;
  border-radius: 4px;
  background: #d9edf7;
  color: #0b4f71;
  font-weight: 700;
}

@media (max-width: 640px) {
  .notification-detail-header {
    display: block;
  }

  .notification-actions {
    margin-top: 0.75rem;
    justify-content: flex-start;
  }
}
</style>
