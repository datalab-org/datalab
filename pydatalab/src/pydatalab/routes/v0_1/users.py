import json

import pymongo.errors
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.people import DisplayName, EmailStr, Group, Person
from pydatalab.mongo import _get_active_mongo_client, flask_mongo
from pydatalab.permissions import active_users_or_get_only, admin_only

USERS = Blueprint("users", __name__)
GROUPS = Blueprint("groups", __name__)


@USERS.before_request
@active_users_or_get_only
def _(): ...


@GROUPS.before_request
@admin_only
def _(): ...


@GROUPS.route("/groups", methods=["PUT"])
def create_group():
    request_json = request.get_json()

    group_json = {
        "group_id": request_json.get("group_id"),
        "display_name": request_json.get("display_name"),
        "description": request_json.get("description"),
        "group_admins": request_json.get("group_admins"),
    }
    try:
        group = Group(**group_json)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid group data: {str(e)}"}), 400

    try:
        group_immutable_id = flask_mongo.db.groups.insert_one(group.dict()).inserted_id
    except pymongo.errors.DuplicateKeyError:
        return jsonify(
            {"status": "error", "message": f"Group ID {group.group_id} already exists."}
        ), 400

    if group_immutable_id:
        return jsonify({"status": "success", "group_immutable_id": str(group_immutable_id)}), 200

    return jsonify({"status": "error", "message": "Unable to create group."}), 400


@GROUPS.route("/groups", methods=["DELETE"])
def delete_group():
    request_json = request.get_json()

    group_id = request_json.get("immutable_id")
    if group_id is not None:
        result = flask_mongo.db.groups.delete_one({"_id": ObjectId(group_id)})

        if result.deleted_count == 1:
            return jsonify({"status": "success"}), 200

    return jsonify({"status": "error", "message": "Unable to delete group."}), 400


@GROUPS.route("/groups/<group_immutable_id>", methods=["PATCH"])
def add_user_to_group(group_immutable_id):
    request_json = request.get_json()

    user_id = request_json.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "No user ID provided."}), 400

    client = _get_active_mongo_client()
    with client.start_session(causal_consistency=True) as session:
        group_exists = flask_mongo.db.groups.find_one(
            {"_id": ObjectId(group_immutable_id)}, session=session
        )
        if not group_exists:
            return jsonify({"status": "error", "message": "Group does not exist."}), 400

        update_user = flask_mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"groups": group_immutable_id}},
            session=session,
        )

        if not update_user.modified_count == 1:
            return jsonify({"status": "error", "message": "Unable to add user to group."}), 400

    return jsonify({"status": "error", "message": "Unable to add user to group."}), 400


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

    try:
        if display_name:
            update["display_name"] = DisplayName(display_name)

        if contact_email or contact_email in (None, ""):
            if contact_email in ("", None):
                update["contact_email"] = None
            else:
                update["contact_email"] = EmailStr(contact_email)

        if account_status:
            update["account_status"] = account_status

    except ValueError as e:
        return jsonify(
            {"status": "error", "message": f"Invalid display name or email was passed: {str(e)}"}
        ), 400

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


@USERS.route("/search-users/", methods=["GET"])
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
