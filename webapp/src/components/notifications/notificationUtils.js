export function notificationStatus(notification) {
  if (notification.archived_at) return "archived";
  return notification.read_at ? "read" : "unread";
}

export function notificationSummary(notification) {
  return notification.summary || notification.message || "";
}

export function formatNotificationDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleString();
}

export function notificationOccurrences(notification) {
  return [...(notification.occurrences || [])].sort(
    (first, second) => new Date(second.occurred_at) - new Date(first.occurred_at),
  );
}
