import datetime

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.people import Person
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import admin_only, get_default_permissions


def check_manager_cycle(user_id_str, new_manager_id_str):
    visited = set()
    current_id = new_manager_id_str

    while current_id is not None:
        if current_id == user_id_str:
            return True
        if current_id in visited:
            break
        visited.add(current_id)

        try:
            manager = flask_mongo.db.users.find_one({"_id": ObjectId(current_id)})
            if manager and "managers" in manager and manager["managers"]:
                if isinstance(manager["managers"], list) and len(manager["managers"]) > 0:
                    current_id = manager["managers"][0]
                else:
                    break
            else:
                break
        except Exception:
            break

    return False


ADMIN = Blueprint("admins", __name__)


@ADMIN.before_request
@admin_only
def _(): ...


@ADMIN.route("/users")
def get_users():
    users = flask_mongo.db.users.aggregate(
        [
            {"$match": get_default_permissions(user_only=True)},
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "role",
                }
            },
            {
                "$addFields": {
                    "role": {
                        "$cond": {
                            "if": {"$eq": [{"$size": "$role"}, 0]},
                            "then": "user",
                            "else": {"$arrayElemAt": ["$role.role", 0]},
                        }
                    },
                }
            },
        ]
    )

    users_list = list(users)

    for user in users_list:
        if "managers" not in user:
            user["managers"] = []
        elif not isinstance(user["managers"], list):
            user["managers"] = []

    return jsonify({"status": "success", "data": [Person(**d).dict() for d in users_list]})


@ADMIN.route("/roles/<user_id>", methods=["PATCH"])
def save_role(user_id):
    request_json = request.get_json()

    if request_json is not None:
        user_role = request_json

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (jsonify({"status": "error", "message": "No user authenticated."}), 401)

    if not CONFIG.TESTING and current_user.role != "admin":
        return (
            jsonify({"status": "error", "message": "User not allowed to edit this profile."}),
            403,
        )

    existing_user = flask_mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if not existing_user:
        return (jsonify({"status": "error", "message": "User not found."}), 404)

    existing_role = flask_mongo.db.roles.find_one({"_id": ObjectId(user_id)})

    if not existing_role:
        if not user_role:
            return (jsonify({"status": "error", "message": "Role not provided for new user."}), 400)

        new_user_role = {"_id": ObjectId(user_id), **user_role}
        flask_mongo.db.roles.insert_one(new_user_role)

        return (jsonify({"status": "success", "message": "New user's role created."}), 201)

    update_result = flask_mongo.db.roles.update_one({"_id": ObjectId(user_id)}, {"$set": user_role})

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


@ADMIN.route("/users/<user_id>/managers", methods=["PATCH"])
def update_user_managers(user_id):
    """Update the managers for a specific user using ObjectIds"""

    request_json = request.get_json()

    if request_json is None or "managers" not in request_json:
        return jsonify({"status": "error", "message": "Managers list not provided"}), 400

    managers = request_json["managers"]

    if not isinstance(managers, list):
        return jsonify({"status": "error", "message": "Managers must be a list"}), 400

    existing_user = flask_mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    manager_object_ids = []
    for manager_id in managers:
        if manager_id:
            try:
                manager_oid = ObjectId(manager_id)
            except Exception:
                return jsonify(
                    {"status": "error", "message": f"Invalid manager ID format: {manager_id}"}
                ), 400

            if not flask_mongo.db.users.find_one({"_id": manager_oid}):
                return jsonify(
                    {"status": "error", "message": f"Manager with ID {manager_id} not found"}
                ), 404

            if check_manager_cycle(user_id, manager_id):
                return jsonify(
                    {
                        "status": "error",
                        "message": "Cannot assign manager: would create a circular management hierarchy",
                    }
                ), 400

            manager_object_ids.append(str(manager_oid))

    update_result = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"managers": manager_object_ids}}
    )

    if update_result.matched_count != 1:
        return jsonify({"status": "error", "message": "Unable to update user managers"}), 400

    return jsonify({"status": "success"}), 200


@ADMIN.route("/items/<refcode>/invalidate-access-token", methods=["POST"])
def invalidate_access_token(refcode: str):
    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    query = {"refcode": refcode, "active": True, "type": "access_token"}

    response = flask_mongo.db.api_keys.update_one(
        query,
        {
            "$set": {
                "active": False,
                "invalidated_at": datetime.datetime.now(tz=datetime.timezone.utc),
                "invalidated_by": ObjectId(current_user.id),
            }
        },
    )

    if response.modified_count == 1:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "detail": "Token not found or already invalidated"}), 404


@ADMIN.route("/access-tokens", methods=["GET"])
def list_access_tokens():
    """List all access tokens with their status and metadata."""

    pipeline = [
        {"$match": {"type": "access_token"}},
        {
            "$lookup": {
                "from": "items",
                "localField": "refcode",
                "foreignField": "refcode",
                "as": "item_info",
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {
            "$project": {
                "_id": 1,
                "refcode": 1,
                "active": 1,
                "created_at": 1,
                "invalidated_at": 1,
                "token": "$token",
                "item_name": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$item_info"}, 0]},
                        "then": {"$arrayElemAt": ["$item_info.name", 0]},
                        "else": None,
                    }
                },
                "item_id": {"$arrayElemAt": ["$item_info.item_id", 0]},
                "item_type": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$item_info"}, 0]},
                        "then": {"$arrayElemAt": ["$item_info.type", 0]},
                        "else": "deleted",
                    }
                },
                "created_by": {"$arrayElemAt": ["$user_info.display_name", 0]},
                "created_by_info": {"$arrayElemAt": ["$user_info", 0]},
            }
        },
        {"$sort": {"created_at": -1}},
    ]

    tokens = list(flask_mongo.db.api_keys.aggregate(pipeline))

    return jsonify({"status": "success", "tokens": tokens}), 200
