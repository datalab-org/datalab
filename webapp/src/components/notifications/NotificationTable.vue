<template>
  <DynamicDataTable
    :columns="columns"
    :data="tableData"
    :data-type="adminMode ? 'adminNotifications' : 'notifications'"
    :global-filter-fields="['title', 'summary', 'message', 'notification_status']"
    :show-buttons="false"
    :row-navigation="false"
    :test-id="adminMode ? 'admin-notification-table' : 'notification-table'"
    @row-click="$emit('row-click', $event)"
    @notification-deleted="$emit('notification-deleted', $event)"
  />
</template>

<script>
import { FilterMatchMode, FilterOperator } from "@primevue/core/api";

import DateRangeFilter from "@/components/DateRangeFilter.vue";
import DynamicDataTable from "@/components/DynamicDataTable.vue";
import SingleSelectFilter from "@/components/SingleSelectFilter.vue";
import TextFilter from "@/components/TextFilter.vue";
import NotificationAdminActionsCell from "@/components/notifications/NotificationAdminActionsCell.vue";
import NotificationUserCell from "@/components/notifications/NotificationUserCell.vue";
import {
  formatNotificationDate,
  notificationStatus,
  notificationSummary,
} from "@/components/notifications/notificationUtils.js";

export default {
  name: "NotificationTable",
  components: { DynamicDataTable },
  props: {
    notifications: { type: Array, default: null },
    adminMode: { type: Boolean, default: false },
  },
  emits: ["row-click", "notification-deleted"],
  computed: {
    tableData() {
      if (this.notifications === null) return null;
      return this.notifications.map((notification) => ({
        ...notification,
        notification_status: notificationStatus(notification),
      }));
    },
    columns() {
      const columns = [
        {
          field: "created_at",
          header: "Sent at",
          getValue: (row) => formatNotificationDate(row.created_at),
          filter: {
            component: DateRangeFilter,
            matchMode: "dateRange",
            operator: FilterOperator.AND,
            noOperator: true,
          },
        },
      ];

      if (this.adminMode) {
        columns.push({
          field: "recipient_info",
          header: "Recipient",
          sortable: false,
          body: {
            component: NotificationUserCell,
            props: (row) => ({ user: row.recipient_info, fallback: "Unknown user" }),
          },
        });
      }

      columns.push(
        {
          field: "title",
          header: "Title",
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search titles" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "summary",
          header: "Summary",
          getValue: notificationSummary,
          cellClass: "notification-summary-cell",
          sortable: false,
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search summaries" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "level",
          header: "Level",
          getValue: (row) => this.capitalize(row.level),
          filter: {
            component: SingleSelectFilter,
            componentProps: { placeholder: "Any", showClear: true },
            matchMode: FilterMatchMode.EQUALS,
            operator: FilterOperator.OR,
            options: () => ["low", "normal", "important", "urgent", "critical"],
          },
        },
        {
          field: "notification_status",
          header: "Status",
          getValue: (row) => this.capitalize(row.notification_status),
          filter: {
            component: SingleSelectFilter,
            componentProps: { placeholder: "Any", showClear: true },
            matchMode: FilterMatchMode.EQUALS,
            operator: FilterOperator.OR,
            options: () => ["unread", "read", "archived"],
          },
        },
        {
          field: "occurrence_count",
          header: "Occurrences",
        },
        {
          field: "last_occurred_at",
          header: "Last occurrence",
          getValue: (row) => formatNotificationDate(row.last_occurred_at),
        },
        {
          field: "created_by_info",
          header: "Created by",
          sortable: false,
          body: {
            component: NotificationUserCell,
            props: (row) => ({ user: row.created_by_info, fallback: "System" }),
          },
        },
      );

      if (this.adminMode) {
        columns.push({
          field: "actions",
          header: "Actions",
          sortable: false,
          body: {
            component: NotificationAdminActionsCell,
            props: (row) => ({ notification: row }),
            events: ["notification-deleted"],
          },
        });
      }

      return columns;
    },
  },
  methods: {
    capitalize(value) {
      return value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
    },
  },
};
</script>

<style scoped>
:deep(.notification-summary-cell) {
  display: -webkit-box;
  max-width: 28rem;
  overflow: hidden;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
</style>
