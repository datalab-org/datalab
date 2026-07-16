from flask import Flask


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


def test_notifications_routes_not_registered_when_disabled(monkeypatch):
    from pydatalab.config import CONFIG
    from pydatalab.main import register_endpoints

    monkeypatch.setattr(CONFIG, "ENABLE_NOTIFICATIONS", False)

    app = Flask("notifications-disabled")
    register_endpoints(app)

    assert not any("/notifications" in str(rule) for rule in app.url_map.iter_rules())
