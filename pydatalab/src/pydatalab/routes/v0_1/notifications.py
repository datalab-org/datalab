from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from flask import Blueprint, abort, jsonify, request
from flask_login import current_user
from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from werkzeug.exceptions import BadRequest, NotFound

from pydatalab.feature_flags import FEATURE_FLAGS
from pydatalab.models.notifications import Notification
from pydatalab.models.people import AccountStatus
from pydatalab.mongo import flask_mongo
from pydatalab.notifications import create_notification_with_result
from pydatalab.permissions import (
    active_users_or_get_only,
    admin_only,
    notification_recipient_only,
    with_notification_permissions,
)

NOTIFICATIONS = Blueprint("notifications", __name__)


@NOTIFICATIONS.before_request
def _require_notifications_feature():
    """Gate the whole blueprint behind the `notifications` feature flag."""
    if not FEATURE_FLAGS.notifications.enabled:
        abort(404)


@NOTIFICATIONS.before_request
@active_users_or_get_only
def _(): ...


def _count_unread_notifications(notification_permissions: dict) -> int:
    return flask_mongo.db.notifications.count_documents(
        {**notification_permissions, "archived_at": None, "read_at": None}
    )


@NOTIFICATIONS.route("/notifications", methods=["POST"])
@admin_only
def create_notifications():
    request_json = request.get_json() or {}
    title = str(request_json.get("title", "")).strip()
    message = (
        str(request_json["message"]).strip() if request_json.get("message") is not None else None
    )
    summary = (
        str(request_json["summary"]).strip() if request_json.get("summary") is not None else None
    )

    send_all_users = request_json.get("send_all_users", False) is True
    if send_all_users:
        recipient_ids = [
            user["_id"]
            for user in flask_mongo.db.users.find(
                {"account_status": AccountStatus.ACTIVE.value},
                {"_id": 1},
            )
        ]
    else:
        recipient_ids = []
        missing_recipient_ids = []
        raw_recipient_ids = request_json.get("recipient_ids")
        if raw_recipient_ids is not None:
            if not isinstance(raw_recipient_ids, list):
                raise BadRequest("recipient_ids must be a list.")
            for recipient_id in raw_recipient_ids:
                try:
                    recipient_object_id = ObjectId(recipient_id)
                except Exception as exc:
                    raise BadRequest(f"Invalid recipient_id {recipient_id!r}.") from exc

                if flask_mongo.db.users.find_one(
                    {"_id": recipient_object_id},
                    {"_id": 1},
                ):
                    recipient_ids.append(recipient_object_id)
                else:
                    missing_recipient_ids.append(str(recipient_object_id))
        if missing_recipient_ids:
            raise NotFound(f"Recipient user(s) not found: {', '.join(missing_recipient_ids)}")

    # deduplicate recipient ids. uses a dict here to preserve order.
    recipient_ids = list(dict.fromkeys(recipient_ids))
    if not recipient_ids:
        raise BadRequest("At least one recipient or all-users option must be provided.")

    grouping = request_json.get("grouping")
    if grouping is not None and grouping != {}:
        if not isinstance(grouping, dict):
            raise BadRequest("grouping must be a dict.")
        grouping = dict(grouping)
    else:
        grouping = None

    level = request_json.get("level", "normal")
    created_by = current_user.person.immutable_id

    def create_for_recipients(db_session=None):
        recipient_notification_results = []
        for target_recipient_id in recipient_ids:
            try:
                notification_result = create_notification_with_result(
                    recipient_id=target_recipient_id,
                    title=title,
                    summary=summary,
                    message=message,
                    level=level,
                    created_by=created_by,
                    grouping=grouping,
                    session=db_session,
                )
            except (ValidationError, ValueError) as notification_error:
                raise BadRequest(str(notification_error)) from notification_error

            if notification_result is not None:
                recipient_notification_results.append(notification_result)

        return recipient_notification_results

    try:
        hello = flask_mongo.cx.admin.command("hello")
    except PyMongoError:
        notification_results = create_for_recipients()
    else:
        if hello.get("msg") == "isdbgrid" or "setName" in hello:
            with flask_mongo.cx.start_session() as session:
                with session.start_transaction():
                    notification_results = create_for_recipients(db_session=session)
        else:
            notification_results = create_for_recipients()

    created_count = sum(created for _, created in notification_results)
    grouped_count = len(notification_results) - created_count
    status_code = 201 if created_count else 200

    return jsonify(
        {
            "status": "success",
            "data": [notification.dict() for notification, _ in notification_results],
            "notification_ids": [
                str(notification.immutable_id) for notification, _ in notification_results
            ],
            "created_count": created_count,
            "grouped_count": grouped_count,
        }
    ), status_code


@NOTIFICATIONS.route("/notifications", methods=["GET"])
@with_notification_permissions
def list_notifications(notification_permissions: dict):
    include_archived = request.args.get("include_archived") == "1"
    unread_only = request.args.get("unread_only") == "1"
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, limit)

    query = dict(notification_permissions)
    if not include_archived:
        query["archived_at"] = None
    if unread_only:
        query["read_at"] = None

    notifications = flask_mongo.db.notifications.aggregate(
        [
            {"$match": query},
            {
                "$addFields": {
                    "_is_read": {"$ne": ["$read_at", None]},
                    "_notification_time": {"$ifNull": ["$last_occurred_at", "$created_at"]},
                }
            },
            {"$sort": {"_is_read": 1, "_notification_time": -1, "created_at": -1}},
            {"$limit": limit},
            {"$project": {"_is_read": 0, "_notification_time": 0}},
        ]
    )
    return jsonify(
        {
            "status": "success",
            "data": [Notification(**notification).dict() for notification in notifications],
            "unread_count": _count_unread_notifications(notification_permissions),
        }
    ), 200


@NOTIFICATIONS.route("/notifications/unread-count", methods=["GET"])
@with_notification_permissions
def get_notification_unread_count(notification_permissions: dict):
    return jsonify(
        {
            "status": "success",
            "unread_count": _count_unread_notifications(notification_permissions),
        }
    ), 200


@NOTIFICATIONS.route("/notifications/<notification_id>", methods=["PATCH"])
@notification_recipient_only
def update_notification(
    notification: dict,
    notification_permissions: dict,
):
    notification_query = {"_id": notification["_id"], **notification_permissions}
    request_json = request.get_json() or {}
    update = {}
    unset = {}
    now = datetime.now(tz=timezone.utc)

    if "read" in request_json:
        if request_json["read"] is True:
            update["read_at"] = notification.get("read_at") or now
            if notification.get("occurrences"):
                update["occurrences.$[].is_new"] = False
        else:
            unset["read_at"] = ""

    if "archived" in request_json:
        if request_json["archived"] is True:
            update["archived_at"] = notification.get("archived_at") or now
        else:
            unset["archived_at"] = ""

    if not update and not unset:
        return jsonify(
            {
                "status": "success",
                "data": Notification(**notification).dict(),
                "message": "No update to perform.",
            }
        ), 200

    mongo_update: dict[str, Any] = {}
    if update:
        mongo_update["$set"] = update
    if unset:
        mongo_update["$unset"] = unset

    updated_notification = flask_mongo.db.notifications.find_one_and_update(
        notification_query,
        mongo_update,
        return_document=ReturnDocument.AFTER,
    )
    if updated_notification is None:
        raise NotFound("Notification not found.")

    return jsonify(
        {
            "status": "success",
            "data": Notification(**updated_notification).dict(),
            "unread_count": _count_unread_notifications(notification_permissions),
        }
    ), 200


@NOTIFICATIONS.route("/notifications/mark-all-read", methods=["POST"])
@with_notification_permissions
def mark_all_notifications_read(notification_permissions: dict):
    now = datetime.now(tz=timezone.utc)
    unread_query = {**notification_permissions, "archived_at": None, "read_at": None}
    grouped_result = flask_mongo.db.notifications.update_many(
        {**unread_query, "occurrences.0": {"$exists": True}},
        {"$set": {"read_at": now, "occurrences.$[].is_new": False}},
    )
    non_grouped_result = flask_mongo.db.notifications.update_many(
        {**unread_query, "occurrences.0": {"$exists": False}},
        {"$set": {"read_at": now}},
    )

    return jsonify(
        {
            "status": "success",
            "modified_count": grouped_result.modified_count + non_grouped_result.modified_count,
            "unread_count": 0,
        }
    ), 200


@NOTIFICATIONS.route("/notifications/<notification_id>", methods=["DELETE"])
@notification_recipient_only
def delete_notification(
    notification: dict,
    notification_permissions: dict,
):
    result = flask_mongo.db.notifications.delete_one(
        {"_id": notification["_id"], **notification_permissions}
    )
    if result.deleted_count == 0:
        raise NotFound("Notification not found.")

    return jsonify(
        {
            "status": "success",
            "deleted_count": result.deleted_count,
            "unread_count": _count_unread_notifications(notification_permissions),
        }
    ), 200
