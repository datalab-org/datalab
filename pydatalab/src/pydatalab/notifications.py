from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models.notifications import (
    Notification,
    NotificationGrouping,
    NotificationGroupPolicy,
    NotificationLevel,
    NotificationOccurrence,
)
from pydatalab.models.utils import PyObjectId
from pydatalab.mongo import flask_mongo


def _max_level(
    current_level: NotificationLevel | str | None, new_level: NotificationLevel | str
) -> str:
    new_notification_level = NotificationLevel(new_level)
    if current_level is None:
        return new_notification_level.value

    current_notification_level = NotificationLevel(current_level)
    if new_notification_level.priority > current_notification_level.priority:
        return new_notification_level.value

    return current_notification_level.value


def _find_grouped_notification(
    *,
    recipient_id: ObjectId,
    title: str,
    grouping: NotificationGrouping,
    now: datetime,
    session: Any | None = None,
) -> dict | None:
    query: dict[str, object] = {
        "recipient_id": recipient_id,
        "title": title,
        "grouping.key": grouping.key,
        "grouping.policy": grouping.policy,
        "$expr": {"$lt": ["$occurrence_count", "$grouping.max_occurrences"]},
        "archived_at": None,
    }
    if NotificationGroupPolicy(grouping.policy) == NotificationGroupPolicy.WINDOW:
        query["grouping.window_seconds"] = grouping.window_seconds
        query["last_occurred_at"] = {
            "$gte": now - timedelta(seconds=int(grouping.window_seconds or 0))
        }

    return flask_mongo.db.notifications.find_one(
        query,
        sort=[("last_occurred_at", -1), ("created_at", -1)],
        session=session,
    )


def _insert_notification(notification: Notification, *, session: Any | None = None) -> Notification:
    result = flask_mongo.db.notifications.insert_one(
        notification.dict(by_alias=True, exclude_none=True),
        session=session,
    )
    notification.immutable_id = result.inserted_id
    return notification


def create_notification_with_result(
    *,
    recipient_id: str | ObjectId | PyObjectId,
    title: str,
    message: str | None = None,
    summary: str | None = None,
    level: NotificationLevel | str = NotificationLevel.NORMAL,
    created_by: str | ObjectId | PyObjectId | None = None,
    grouping: NotificationGrouping | dict[str, object] | None = None,
    session: Any | None = None,
) -> tuple[Notification, bool] | None:
    """Create or group an in-app notification if the feature is enabled.

    Returns:
        A tuple of ``(notification, created)`` when a notification is created or
        grouped. ``created`` is ``True`` when a new notification document was
        inserted and ``False`` when the notification was folded into an existing
        grouped notification. Returns ``None`` when notifications are disabled.
    """

    if not CONFIG.ENABLE_NOTIFICATIONS:
        LOGGER.debug("Notifications are disabled; not creating notification %r", title)
        return None

    now = datetime.now(tz=timezone.utc)
    recipient_object_id = ObjectId(recipient_id)

    if grouping is None:
        notification = Notification(
            recipient_id=recipient_object_id,
            title=title,
            summary=summary,
            message=message,
            level=level,
            created_by=ObjectId(created_by) if created_by else None,
            occurrence_count=1,
            last_occurred_at=now,
        )
        return _insert_notification(notification, session=session), True

    if isinstance(grouping, dict):
        grouping = NotificationGrouping(**grouping)

    occurrence = NotificationOccurrence(
        occurred_at=now,
        message=message,
        summary=summary,
        level=level,
        is_new=True,
    )
    grouped_notification = _find_grouped_notification(
        recipient_id=recipient_object_id,
        title=title,
        grouping=grouping,
        now=now,
        session=session,
    )

    if grouped_notification is not None:
        mongo_update = {
            "$inc": {"occurrence_count": 1},
            "$set": {
                "message": message,
                "summary": summary,
                "last_occurred_at": now,
                "level": _max_level(grouped_notification.get("level"), level),
            },
            "$push": {"occurrences": occurrence.dict(exclude_none=True)},
            "$unset": {"read_at": ""},
        }
        updated_notification = flask_mongo.db.notifications.find_one_and_update(
            {"_id": grouped_notification["_id"]},
            mongo_update,
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return Notification(**updated_notification), False

    notification = Notification(
        recipient_id=recipient_object_id,
        title=title,
        summary=summary,
        message=message,
        level=level,
        created_by=ObjectId(created_by) if created_by else None,
        grouping=grouping,
        occurrence_count=1,
        last_occurred_at=now,
        occurrences=[occurrence],
    )

    return _insert_notification(notification, session=session), True


def create_notification(
    *,
    recipient_id: str | ObjectId | PyObjectId,
    title: str,
    message: str | None = None,
    summary: str | None = None,
    level: NotificationLevel | str = NotificationLevel.NORMAL,
    created_by: str | ObjectId | PyObjectId | None = None,
    grouping: NotificationGrouping | dict[str, object] | None = None,
) -> Notification | None:
    """Create an in-app notification if the feature is enabled.

    This helper is safe for future ingestion/admin callers: when notifications
    are disabled it returns ``None`` without touching MongoDB.
    """

    result = create_notification_with_result(
        recipient_id=recipient_id,
        title=title,
        summary=summary,
        message=message,
        level=level,
        created_by=created_by,
        grouping=grouping,
    )
    if result is None:
        return None

    notification, _ = result
    return notification
