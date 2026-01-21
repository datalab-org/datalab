import json
from datetime import datetime
from datetime import timedelta as td
from datetime import timezone as tz

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models.people import AccountStatus, DisplayName, EmailStr, Person
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only
from pydatalab.routes.v0_1.auth import _generate_and_store_token, _send_magic_link_email

USERS = Blueprint("users", __name__)


@USERS.before_request
@active_users_or_get_only
def _(): ...


@USERS.route("/users/<user_id>", methods=["PATCH"])
def save_user(user_id):
    request_json = request.get_json()

    display_name: str | None = None
    contact_email: str | None = None
    account_status: str | None = None

    if request_json is not None:
        display_name = request_json.get("display_name", False)
        contact_email = request_json.get("contact_email", False)
        account_status = request_json.get("account_status", None)

    if not current_user.is_authenticated and not CONFIG.TESTING:
        raise Unauthorized("No user authenticated.")

    if not CONFIG.TESTING and current_user.id != user_id and current_user.role != "admin":
        raise Forbidden("Current user not allowed to edit this profile.")

    update = {}

    try:
        if display_name:
            update["display_name"] = DisplayName(display_name)

    except ValueError:
        raise BadRequest(f"Invalid display name {display_name!r} was passed")

    try:
        if contact_email or contact_email in (None, ""):
            if contact_email in ("", None):
                update["contact_email"] = None
            else:
                update["contact_email"] = EmailStr(contact_email)

    except ValueError:
        raise BadRequest(f"Invalid email address {contact_email!r} was passed")

    trigger_email_verification = False
    if update.get("contact_email"):
        # Check if this email identity already exists for this user
        existing_email_identity = False
        if update.get("contact_email") is not None:
            existing_email_identity = flask_mongo.db.users.find_one(
                {
                    "_id": ObjectId(user_id),
                    "identities": {"$elemMatch": {"type": "email", "identifier": contact_email}},
                }
            )
            if not existing_email_identity:
                # If not, push it as a new unverified identity
                flask_mongo.db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {
                            "identities": {
                                "identity_type": "email",
                                "identifier": contact_email,
                                "name": contact_email,
                                "verified": False,
                            }
                        }
                    },
                )
                trigger_email_verification = True

        if existing_email_identity and not existing_email_identity.get("verified"):
            # If this did exist, but is not yet verified, also trigger an email
            trigger_email_verification = True

        if trigger_email_verification:
            token = _generate_and_store_token(
                email=contact_email,
                intent="verify",
            )
            try:
                _send_magic_link_email(
                    email=contact_email,
                    token=token,
                    referrer=CONFIG.APP_URL,
                    purpose="verify",
                )
            except RuntimeError as e:
                trigger_email_verification = False
                LOGGER.critical("Unable to send verification email on this deployment: %s", e)

    try:
        if account_status:
            update["account_status"] = AccountStatus(account_status)
    except ValueError:
        raise BadRequest(f"Invalid account status {account_status!r} was passed")

    if not update:
        return jsonify({"status": "success", "message": "No update to perform."}), 200

    update_result = flask_mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})

    if update_result.matched_count != 1:
        raise BadRequest("Unable to update user.")

    if trigger_email_verification:
        return (
            jsonify(
                {"message": f"Verification email sent to {contact_email}", "status": "success"}
            ),
            200,
        )

    return (jsonify({"message": "User updated successfully", "status": "success"}), 200)


@USERS.route("/users/<user_id>/activity", methods=["GET"])
@active_users_or_get_only
def get_user_activity(user_id):
    """Get activity data for a specific user (creation dates)."""

    if str(current_user.person.immutable_id) != user_id and current_user.role != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    months = int(request.args.get("months", 12))

    start_date = datetime.now(tz=tz.utc) - td(days=30 * months)
    end_date = datetime.now(tz=tz.utc)

    try:
        user_object_id = ObjectId(user_id)
        creator_match = user_object_id
    except Exception:
        creator_match = user_id

    pipeline = [
        {"$match": {"creator_ids": creator_match, "date": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    activity_data = list(flask_mongo.db.items.aggregate(pipeline))

    result = {date_entry["_id"]: date_entry["count"] for date_entry in activity_data}

    return jsonify({"status": "success", "data": result}), 200


@USERS.route("/search-users/", methods=["GET"])
@USERS.route("/search/users/", methods=["GET"])
def search_users():
    """Perform free text search on users and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of  (default 100)

    Returns:
        response list of dictionaries containing the matching items in order of
        descending match score.
    """

    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    types = request.args.get("types", default=None)

    match_obj = {"$text": {"$search": query}}
    if types is not None:
        match_obj["type"] = {"$in": types}

    cursor = flask_mongo.db.users.aggregate(
        [
            {"$match": match_obj},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": nresults},
            {
                "$project": {
                    "_id": 1,
                    "identities": 1,
                    "display_name": 1,
                    "contact_email": 1,
                }
            },
        ]
    )
    return jsonify(
        {"status": "success", "users": list(json.loads(Person(**d).json()) for d in cursor)}
    ), 200
