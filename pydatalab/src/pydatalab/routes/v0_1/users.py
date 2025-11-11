from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest

from pydatalab.config import CONFIG
from pydatalab.models.people import Person
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only

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
        return (jsonify({"status": "error", "message": "No user authenticated."}), 401)

    if not CONFIG.TESTING and current_user.id != user_id and current_user.role != "admin":
        return (
            jsonify({"status": "error", "message": "User not allowed to edit this profile."}),
            403,
        )

    update = {}

    if display_name:
        update["display_name"] = display_name

    if contact_email or contact_email in (None, ""):
        if contact_email in ("", None):
            update["contact_email"] = None
        else:
            update["contact_email"] = contact_email

    if account_status:
        update["account_status"] = account_status

    try:
        _ = Person(**update)
    except ValidationError as e:
        raise BadRequest(f"Invalid user data: {e.errors()}") from e

    if not update:
        return jsonify({"status": "success", "message": "No update was performed."}), 200

    update_result = flask_mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})

    if update_result.matched_count != 1:
        return (jsonify({"status": "error", "message": "Unable to update user."}), 400)

    if update_result.modified_count != 1:
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "No update was performed",
                }
            ),
            200,
        )

    return (jsonify({"status": "success"}), 200)
