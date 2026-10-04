from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

from pydatalab.models.people import AccountStatus


@pytest.fixture(autouse=True)
def clean_notifications(database):
    database.notifications.delete_many({})


def _create_notification(client, recipient_id, **overrides):
    payload = {
        "recipient_ids": [str(recipient_id)],
        "title": "Ingestion warning",
        "message": "A generated notification for testing.",
        "level": "important",
        **overrides,
    }
    return client.post("/notifications", json=payload)


def test_create_and_list(
    admin_client, client, another_client, user_id, another_user_id, admin_user_id
):
    resp = admin_client.post(
        "/notifications",
        json={
            "recipient_ids": [str(user_id), str(another_user_id)],
            "title": "Batch import warning",
            "summary": "Two rows failed.",
            "message": "Two rows could not be matched.",
            "level": "important",
        },
    )

    assert resp.status_code == 201
    assert len(resp.json["data"]) == 2
    assert resp.json["created_count"] == 2
    assert resp.json["grouped_count"] == 0

    resp = client.get("/notifications")

    assert resp.status_code == 200
    assert resp.json["unread_count"] == 1
    assert len(resp.json["data"]) == 1
    notification = resp.json["data"][0]
    assert notification["recipient_id"] == str(user_id)
    assert notification["created_by"] == str(admin_user_id)
    assert notification["title"] == "Batch import warning"
    assert notification["summary"] == "Two rows failed."
    assert notification["message"] == "Two rows could not be matched."
    assert notification["level"] == "important"
    assert notification["read_at"] is None
    assert notification["archived_at"] is None
    assert notification["occurrence_count"] == 1
    assert notification.get("occurrences") is None

    resp = admin_client.get("/notifications")
    assert resp.status_code == 200
    assert resp.json["unread_count"] == 0
    assert resp.json["data"] == []

    resp = another_client.get("/notifications")
    assert resp.status_code == 200
    assert resp.json["unread_count"] == 1
    assert resp.json["data"][0]["recipient_id"] == str(another_user_id)


def test_send_all_users_precedence(admin_client, database):
    active_user_ids = {
        str(user["_id"])
        for user in database.users.find(
            {"account_status": AccountStatus.ACTIVE.value},
            {"_id": 1},
        )
    }

    resp = admin_client.post(
        "/notifications",
        json={
            "recipient_ids": ["not-an-object-id"],
            "send_all_users": True,
            "title": "Scheduled maintenance",
        },
    )

    assert resp.status_code == 201
    assert resp.json["created_count"] == len(active_user_ids)
    assert resp.json["grouped_count"] == 0
    assert {notification["recipient_id"] for notification in resp.json["data"]} == active_user_ids
    assert database.notifications.count_documents({}) == len(active_user_ids)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {"recipient_ids": [], "title": "No recipients"},
            "At least one recipient or all-users option must be provided.",
        ),
        (
            {"recipient_ids": "not-a-list", "title": "Recipient IDs must be a list"},
            "recipient_ids must be a list.",
        ),
        (
            {"recipient_ids": ["not-an-object-id"], "title": "Malformed recipient ID"},
            "Invalid recipient_id 'not-an-object-id'.",
        ),
    ],
)
def test_create_validation_errors(admin_client, database, payload, message):
    resp = admin_client.post("/notifications", json=payload)

    assert resp.status_code == 400
    assert resp.json["message"] == message
    assert database.notifications.count_documents({}) == 0


def test_create_missing_recipient(admin_client, database):
    missing_id = str(ObjectId())

    resp = admin_client.post(
        "/notifications",
        json={"recipient_ids": [missing_id], "title": "Missing recipient"},
    )

    assert resp.status_code == 404
    assert resp.json["message"] == f"Recipient user(s) not found: {missing_id}"
    assert database.notifications.count_documents({}) == 0


def test_create_requires_admin(client, user_id, database):
    resp = _create_notification(client, user_id)

    assert resp.status_code == 403
    assert database.notifications.count_documents({}) == 0


def test_read_archive_filters(admin_client, client, another_client, user_id):
    create_resp = _create_notification(admin_client, user_id)
    assert create_resp.status_code == 201
    notification_id = create_resp.json["notification_ids"][0]

    resp = another_client.patch(f"/notifications/{notification_id}", json={"read": True})
    assert resp.status_code == 404
    assert resp.json["error"] == "Notification not found."

    before = datetime.now(tz=timezone.utc)
    resp = client.patch(f"/notifications/{notification_id}", json={"read": True})
    after = datetime.now(tz=timezone.utc)

    assert resp.status_code == 200
    read_at = datetime.fromisoformat(resp.json["data"]["read_at"])
    if read_at.tzinfo is None:
        read_at = read_at.replace(tzinfo=timezone.utc)
    assert before <= read_at <= after
    assert resp.json["unread_count"] == 0

    resp = client.patch(f"/notifications/{notification_id}", json={"read": False})
    assert resp.status_code == 200
    assert resp.json["data"]["read_at"] is None
    assert resp.json["unread_count"] == 1

    before = datetime.now(tz=timezone.utc)
    resp = client.patch(f"/notifications/{notification_id}", json={"archived": True})
    after = datetime.now(tz=timezone.utc)

    assert resp.status_code == 200
    archived_at = datetime.fromisoformat(resp.json["data"]["archived_at"])
    if archived_at.tzinfo is None:
        archived_at = archived_at.replace(tzinfo=timezone.utc)
    assert before <= archived_at <= after
    assert resp.json["unread_count"] == 0

    resp = client.get("/notifications")
    assert resp.status_code == 200
    assert resp.json["data"] == []

    resp = client.get("/notifications?include_archived=1")
    assert resp.status_code == 200
    assert len(resp.json["data"]) == 1


def test_delete_own_only(admin_client, client, another_client, database, user_id):
    create_resp = _create_notification(admin_client, user_id)
    assert create_resp.status_code == 201
    notification_id = create_resp.json["notification_ids"][0]

    resp = another_client.delete(f"/notifications/{notification_id}")
    assert resp.status_code == 404
    assert resp.json["error"] == "Notification not found."

    resp = client.delete(f"/notifications/{notification_id}")

    assert resp.status_code == 200
    assert resp.json["deleted_count"] == 1
    assert resp.json["unread_count"] == 0
    assert database.notifications.count_documents({"recipient_id": user_id}) == 0


def test_mark_all_read(admin_client, client, another_client, user_id, another_user_id):
    first_resp = _create_notification(admin_client, user_id, title="First")
    second_resp = _create_notification(admin_client, user_id, title="Second")
    other_user_resp = _create_notification(admin_client, another_user_id, title="Other user")
    assert first_resp.status_code == 201
    assert second_resp.status_code == 201
    assert other_user_resp.status_code == 201
    grouped_resp = _create_notification(
        admin_client,
        user_id,
        title="Grouped mark all",
        grouping={"key": "ingestion:mark-all", "policy": "once"},
    )
    assert grouped_resp.status_code == 201
    grouped_resp = _create_notification(
        admin_client,
        user_id,
        title="Grouped mark all",
        grouping={"key": "ingestion:mark-all", "policy": "once"},
    )
    assert grouped_resp.status_code == 200
    assert [occurrence["is_new"] for occurrence in grouped_resp.json["data"][0]["occurrences"]] == [
        True,
        True,
    ]

    resp = client.get("/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json["unread_count"] == 3

    resp = client.post("/notifications/mark-all-read")

    assert resp.status_code == 200
    assert resp.json["modified_count"] == 3
    assert resp.json["unread_count"] == 0

    resp = client.get("/notifications")
    grouped_notification = next(
        notification
        for notification in resp.json["data"]
        if notification["title"] == "Grouped mark all"
    )
    assert [occurrence["is_new"] for occurrence in grouped_notification["occurrences"]] == [
        False,
        False,
    ]

    resp = client.get("/notifications?unread_only=1")
    assert resp.status_code == 200
    assert resp.json["data"] == []

    resp = another_client.get("/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json["unread_count"] == 1


def test_list_unread_first(admin_client, client, user_id):
    read_resp = _create_notification(admin_client, user_id, title="Read first")
    assert read_resp.status_code == 201
    read_notification_id = read_resp.json["notification_ids"][0]
    client.patch(f"/notifications/{read_notification_id}", json={"read": True})
    unread_resp = _create_notification(admin_client, user_id, title="Unread second")
    assert unread_resp.status_code == 201

    resp = client.get("/notifications")

    assert resp.status_code == 200
    assert [notification["title"] for notification in resp.json["data"]] == [
        "Unread second",
        "Read first",
    ]


def test_grouping_default_window(admin_client, client, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        title="Default grouping",
        grouping={"key": "ingestion:default-window"},
    )
    assert first_resp.status_code == 201
    assert first_resp.json["created_count"] == 1
    assert first_resp.json["grouped_count"] == 0

    second_resp = _create_notification(
        admin_client,
        user_id,
        title="Default grouping",
        grouping={"key": "ingestion:default-window"},
    )
    assert second_resp.status_code == 200
    assert second_resp.json["created_count"] == 0
    assert second_resp.json["grouped_count"] == 1

    resp = client.get("/notifications")
    notification = resp.json["data"][0]
    assert notification["grouping"] == {
        "key": "ingestion:default-window",
        "policy": "window",
        "window_seconds": 86400,
        "max_occurrences": 100,
    }
    assert [occurrence["is_new"] for occurrence in notification["occurrences"]] == [True, True]


def test_grouping_once_updates_existing(admin_client, client, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        title="Equipment anomaly",
        summary="Equipment drift detected in run 1.",
        message="The first ingestion run detected drift.",
        level="low",
        grouping={"key": "ingestion:equipment:eq-1", "policy": "once"},
    )
    assert first_resp.status_code == 201
    notification_id = first_resp.json["notification_ids"][0]

    resp = client.get("/notifications")
    assert len(resp.json["data"]) == 1
    assert resp.json["data"][0]["read_at"] is None
    assert [occurrence["is_new"] for occurrence in resp.json["data"][0]["occurrences"]] == [True]
    assert resp.json["unread_count"] == 1

    resp = client.patch(f"/notifications/{notification_id}", json={"read": True})
    assert resp.status_code == 200
    assert resp.json["data"]["read_at"] is not None
    assert [occurrence["is_new"] for occurrence in resp.json["data"]["occurrences"]] == [False]

    resp = client.get("/notifications")
    assert resp.json["unread_count"] == 0
    assert [occurrence["is_new"] for occurrence in resp.json["data"][0]["occurrences"]] == [False]

    second_resp = _create_notification(
        admin_client,
        user_id,
        title="Equipment anomaly",
        summary="Equipment drift detected in run 2.",
        message="The second ingestion run detected drift.",
        level="critical",
        grouping={"key": "ingestion:equipment:eq-1", "policy": "once"},
    )
    third_resp = _create_notification(
        admin_client,
        user_id,
        title="Equipment anomaly",
        summary="Equipment drift detected in run 3.",
        message="The third ingestion run detected drift.",
        level="normal",
        grouping={"key": "ingestion:equipment:eq-1", "policy": "once"},
    )

    assert second_resp.status_code == 200
    assert third_resp.status_code == 200
    assert third_resp.json["notification_ids"] == [notification_id]

    resp = client.get("/notifications")

    assert resp.status_code == 200
    assert resp.json["unread_count"] == 1
    assert len(resp.json["data"]) == 1
    notification = resp.json["data"][0]
    assert notification["summary"] == "Equipment drift detected in run 3."
    assert notification["message"] == "The third ingestion run detected drift."
    assert notification["level"] == "critical"
    assert notification["read_at"] is None
    assert notification["occurrence_count"] == 3
    assert [occurrence["level"] for occurrence in notification["occurrences"]] == [
        "low",
        "critical",
        "normal",
    ]
    assert [occurrence["is_new"] for occurrence in notification["occurrences"]] == [
        False,
        True,
        True,
    ]
    assert notification["occurrences"][0]["message"] == "The first ingestion run detected drift."
    assert notification["occurrences"][2]["message"] == "The third ingestion run detected drift."


def test_grouping_archived_creates_new_document(admin_client, client, database, user_id):
    resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:archived", "policy": "once"},
    )
    assert resp.status_code == 201
    notification_id = resp.json["notification_ids"][0]
    client.patch(f"/notifications/{notification_id}", json={"archived": True})

    resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:archived", "policy": "once"},
    )

    assert resp.status_code == 201
    second_notification_id = resp.json["notification_ids"][0]
    assert resp.json["notification_ids"] != [notification_id]
    assert database.notifications.count_documents({"recipient_id": user_id}) == 2

    resp = client.get("/notifications?include_archived=1")
    assert len(resp.json["data"]) == 2

    resp = client.get("/notifications")
    assert len(resp.json["data"]) == 1
    assert resp.json["data"][0]["immutable_id"] == second_notification_id


def test_grouping_title_separates_documents(admin_client, database, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        title="First title",
        grouping={"key": "ingestion:title", "policy": "once"},
    )
    second_resp = _create_notification(
        admin_client,
        user_id,
        title="Second title",
        grouping={"key": "ingestion:title", "policy": "once"},
    )

    assert first_resp.status_code == 201
    assert second_resp.status_code == 201
    assert database.notifications.count_documents({"recipient_id": user_id}) == 2


def test_grouping_window_expires(admin_client, database, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:pipeline:daily", "policy": "window", "window_seconds": 60},
    )
    assert first_resp.status_code == 201
    first_notification_id = first_resp.json["notification_ids"][0]

    second_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:pipeline:daily", "policy": "window", "window_seconds": 60},
    )
    assert second_resp.status_code == 200
    assert second_resp.json["notification_ids"] == [first_notification_id]

    # Manually update the last_occurred_at to be more than 60 seconds ago so that the next notification creates a new document.
    database.notifications.update_one(
        {"_id": ObjectId(first_notification_id)},
        {"$set": {"last_occurred_at": datetime.now(tz=timezone.utc) - timedelta(seconds=120)}},
    )

    third_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:pipeline:daily", "policy": "window", "window_seconds": 60},
    )

    assert third_resp.status_code == 201
    assert third_resp.json["created_count"] == 1
    assert database.notifications.count_documents({"recipient_id": user_id}) == 2


def test_grouping_once_uses_stored_cap(admin_client, database, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:max-once", "policy": "once", "max_occurrences": 2},
    )
    assert first_resp.status_code == 201
    first_notification_id = first_resp.json["notification_ids"][0]

    second_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:max-once", "policy": "once", "max_occurrences": 100},
    )
    assert second_resp.status_code == 200
    assert second_resp.json["notification_ids"] == [first_notification_id]

    first_notification = database.notifications.find_one({"_id": ObjectId(first_notification_id)})
    assert first_notification["occurrence_count"] == 2
    assert first_notification["grouping"]["max_occurrences"] == 2

    third_resp = _create_notification(
        admin_client,
        user_id,
        grouping={"key": "ingestion:max-once", "policy": "once", "max_occurrences": 100},
    )
    assert third_resp.status_code == 201
    assert third_resp.json["notification_ids"] != [first_notification_id]
    assert third_resp.json["data"][0]["grouping"]["max_occurrences"] == 100
    assert database.notifications.count_documents({"recipient_id": user_id}) == 2


def test_grouping_window_uses_stored_cap(admin_client, database, user_id):
    first_resp = _create_notification(
        admin_client,
        user_id,
        grouping={
            "key": "ingestion:pipeline:max-window",
            "policy": "window",
            "window_seconds": 3600,
            "max_occurrences": 2,
        },
    )
    assert first_resp.status_code == 201
    first_notification_id = first_resp.json["notification_ids"][0]

    second_resp = _create_notification(
        admin_client,
        user_id,
        grouping={
            "key": "ingestion:pipeline:max-window",
            "policy": "window",
            "window_seconds": 3600,
            "max_occurrences": 100,
        },
    )
    assert second_resp.status_code == 200
    assert second_resp.json["notification_ids"] == [first_notification_id]

    first_notification = database.notifications.find_one({"_id": ObjectId(first_notification_id)})
    assert first_notification["occurrence_count"] == 2
    assert first_notification["grouping"]["max_occurrences"] == 2

    third_resp = _create_notification(
        admin_client,
        user_id,
        grouping={
            "key": "ingestion:pipeline:max-window",
            "policy": "window",
            "window_seconds": 3600,
            "max_occurrences": 100,
        },
    )

    assert third_resp.status_code == 201
    assert third_resp.json["notification_ids"] != [first_notification_id]
    assert third_resp.json["data"][0]["grouping"]["max_occurrences"] == 100
    assert database.notifications.count_documents({"recipient_id": user_id}) == 2
