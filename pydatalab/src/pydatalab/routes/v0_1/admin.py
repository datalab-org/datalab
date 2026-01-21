import datetime

import pymongo.errors
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest, NotFound

from pydatalab.config import CONFIG
from pydatalab.models.people import Group, Person
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import admin_only


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
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "role",
                }
            },
            {
                "$lookup": {
                    "from": "groups",
                    "let": {"group_ids": "$group_ids"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$group_ids", []]}]}}},
                        {"$addFields": {"__order": {"$indexOfArray": ["$$group_ids", "$_id"]}}},
                        {"$sort": {"__order": 1}},
                        {"$project": {"_id": 1, "display_name": 1}},
                    ],
                    "as": "groups",
                },
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


@ADMIN.route("/groups", methods=["GET"])
def get_groups():
    # Lookup members from users collection: find all those that refer to this group ID in their groups->immutable_id field
    members_lookup = {
        "from": "users",
        "let": {"group_id": "$_id"},
        "pipeline": [
            {
                "$match": {
                    "$expr": {"$in": ["$$group_id", {"$ifNull": ["$groups.immutable_id", []]}]}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "display_name": 1,
                    "contact_email": 1,
                }
            },
        ],
        "as": "members",
    }

    # Lookup managers from users collection: find all those referred to by ID in this group under the managers field
    managers_lookup = {
        "from": "users",
        "let": {"manager_ids": "$managers"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$manager_ids", []]}]}}},
            {
                "$project": {
                    "_id": 1,
                    "display_name": 1,
                    "contact_email": 1,
                }
            },
        ],
        "as": "managers",
    }

    group_docs = flask_mongo.db.groups.aggregate(
        [{"$match": {}}, {"$lookup": members_lookup}, {"$lookup": managers_lookup}]
    )

    return jsonify({"status": "success", "data": [Group(**d).dict() for d in group_docs]}), 200


@ADMIN.route("/groups", methods=["PUT"])
def create_group():
    request_json = request.get_json()

    group_json = {
        "group_id": request_json.get("group_id"),
        "display_name": request_json.get("display_name"),
        "description": request_json.get("description"),
        "managers": request_json.get("managers"),
    }

    if group_json["group_id"] is None:
        raise BadRequest("Group ID is required to create a new group.")

    if group_json["managers"]:
        group_json["managers"] = [ObjectId(u) for u in request_json["managers"]]

    try:
        group = Group(**group_json)
    except Exception as e:
        raise BadRequest(f"Invalid new group data: {str(e)}")

    bad_managers = [
        m for m in group_json["managers"] if not flask_mongo.db.users.find_one({"_id": ObjectId(m)})
    ]
    if bad_managers:
        raise BadRequest(
            f"Manager(s) with ID(s) {bad_managers} not found; cannot create group {group_json['group_id']}"
        )

    try:
        group_immutable_id = flask_mongo.db.groups.insert_one(
            group.dict(exclude_unset=True)
        ).inserted_id
    except pymongo.errors.DuplicateKeyError:
        return jsonify(
            {"status": "error", "message": f"Group ID {group.group_id} already exists."}
        ), 400

    if group_immutable_id:
        return jsonify({"status": "success", "group_immutable_id": str(group_immutable_id)}), 200

    return jsonify({"status": "error", "message": "Unable to create group."}), 400


@ADMIN.route("/groups/<group_immutable_id>", methods=["DELETE"])
def delete_group(group_immutable_id: str):
    if group_immutable_id is not None:
        result = flask_mongo.db.groups.delete_one({"_id": ObjectId(group_immutable_id)})

        if result.deleted_count == 1:
            return jsonify({"status": "success"}), 200

    return jsonify({"status": "error", "message": "Unable to delete group."}), 400


@ADMIN.route("/groups/<group_immutable_id>", methods=["PATCH"])
def update_group(group_immutable_id: str):
    request_json = request.get_json()

    existing_group = flask_mongo.db.groups.find_one({"_id": ObjectId(group_immutable_id)})
    if not existing_group:
        return jsonify({"status": "error", "message": "Group not found."}), 404

    update_data = {}

    if "display_name" in request_json:
        update_data["display_name"] = request_json["display_name"]

    if "description" in request_json:
        update_data["description"] = request_json["description"]

    if "group_id" in request_json:
        update_data["group_id"] = request_json["group_id"]

    if "managers" in request_json:
        update_data["managers"] = [ObjectId(u) for u in request_json["managers"]]
        bad_managers = [
            m for m in update_data["managers"] if not flask_mongo.db.users.find_one({"_id": m})
        ]
        if bad_managers:
            raise BadRequest(
                f"Manager(s) with ID(s) {bad_managers} not found; cannot update group {group_immutable_id}"
            )

    try:
        temp_group_data = {**existing_group, **update_data}
        temp_group_data.pop("_id", None)
        Group(**temp_group_data)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid group data: {str(e)}"}), 400

    try:
        result = flask_mongo.db.groups.update_one(
            {"_id": ObjectId(group_immutable_id)}, {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Group not found."}), 404

        if result.modified_count == 0:
            return jsonify({"status": "success", "message": "No changes were made."}), 200

        return jsonify({"status": "success", "message": "Group updated successfully."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to update group: {str(e)}"}), 500


@ADMIN.route("/groups/<group_immutable_id>", methods=["PUT"])
def add_user_to_group(group_immutable_id: str):
    request_json = request.get_json()

    user_id = request_json.get("user_id")

    if not user_id:
        raise BadRequest("No user ID provided.")

    group_exists = flask_mongo.db.groups.find_one(
        {"_id": ObjectId(group_immutable_id)},
    )
    if not group_exists:
        raise NotFound("Group does not exist.")

    update_user = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"groups": {"immutable_id": ObjectId(group_immutable_id)}}},
    )

    if update_user.matched_count == 0:
        raise BadRequest("Unable to add user to group: user does not exist.")

    if update_user.modified_count == 0:
        return jsonify({"status": "success", "message": "User already in group."}), 304

    return jsonify({"status": "success", "message": "User added to group."}), 200


@ADMIN.route("/groups/<group_immutable_id>/members/<user_id>", methods=["DELETE"])
def remove_user_from_group(group_immutable_id: str, user_id: str):
    group_exists = flask_mongo.db.groups.find_one(
        {"_id": ObjectId(group_immutable_id)},
    )
    if not group_exists:
        raise NotFound("Group does not exist.")

    update_user = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"groups": {"immutable_id": ObjectId(group_immutable_id)}}},
    )

    if update_user.matched_count == 0:
        raise BadRequest("Unable to remove user from group: user does not exist.")

    # Also remove user from group's managers list if they are a manager
    flask_mongo.db.groups.update_one(
        {"_id": ObjectId(group_immutable_id)},
        {"$pull": {"managers": ObjectId(user_id)}},
    )

    if update_user.modified_count == 0:
        return jsonify({"status": "success", "message": "User was not in group."}), 304

    return jsonify({"status": "success", "message": "User removed from group."}), 200
