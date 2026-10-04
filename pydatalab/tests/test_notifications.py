# This file was edited with the assistance of an AI model and requires human review from the contributor.
import json

import pytest
from bson import ObjectId
from flask import Flask
from pydantic import ValidationError


def test_notification_level_ordering():
    from pydatalab.models.notifications import NotificationLevel

    assert (
        NotificationLevel.LOW.priority
        < NotificationLevel.NORMAL.priority
        < NotificationLevel.IMPORTANT.priority
        < NotificationLevel.URGENT.priority
        < NotificationLevel.CRITICAL.priority
    )


def test_notification_occurrence_new_state_defaults_false():
    from pydatalab.models.notifications import NotificationOccurrence

    assert NotificationOccurrence().is_new is False


def test_notification_grouping_policy_validation():
    from pydatalab.models.notifications import NotificationGrouping

    grouping = NotificationGrouping(key="import:123", policy="once", window_seconds=60)

    assert grouping.window_seconds is None

    with pytest.raises(ValidationError, match="window_seconds must be provided"):
        NotificationGrouping(key="import:123", policy="window", window_seconds=None)


def test_notification_pydantic_v2_serialization():
    from pydatalab.models.notifications import Notification

    recipient_id = ObjectId()
    notification = Notification(recipient_id=recipient_id, title="Import finished")

    mongo_document = notification.model_dump(by_alias=True, exclude_none=True)
    json_document = json.loads(notification.model_dump_json(by_alias=True, exclude_none=True))

    assert mongo_document["recipient_id"] == recipient_id
    assert json_document["recipient_id"] == str(recipient_id)
    assert json_document["type"] == "notifications"
    assert json_document["created_at"].endswith("Z")

    with pytest.raises(ValidationError):
        Notification(type="samples", recipient_id=recipient_id, title="Wrong type")


def test_notifications_routes_not_registered_when_disabled(monkeypatch):
    from pydatalab.config import CONFIG
    from pydatalab.main import register_endpoints

    monkeypatch.setattr(CONFIG, "ENABLE_NOTIFICATIONS", False)

    app = Flask("notifications-disabled")
    register_endpoints(app)

    assert not any("/notifications" in str(rule) for rule in app.url_map.iter_rules())
