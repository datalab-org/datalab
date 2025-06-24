import datetime
import json

import pymongo.errors
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.people import Group, User
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import admin_only

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
                        {"$project": {"_id": 1, "display_name": 1, "group_id": 1, "type": 1}},
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
                    }
                }
            },
        ]
    )

    return jsonify({"status": "success", "data": list(json.loads(User(**u).json()) for u in users)})


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
    groups_data = []
    for group_doc in flask_mongo.db.groups.find():
        group_doc["immutable_id"] = str(group_doc["_id"])

        group_data = json.loads(Group(**group_doc).json())

        group_members = list(
            flask_mongo.db.users.find(
                {"group_ids": group_doc["_id"]}, {"_id": 1, "display_name": 1, "contact_email": 1}
            )
        )
        group_data["members"] = [
            {
                "immutable_id": str(member["_id"]),
                "display_name": member.get("display_name", ""),
                "contact_email": member.get("contact_email", ""),
            }
            for member in group_members
        ]

        if group_doc.get("group_admins"):
            admin_ids = [ObjectId(admin_id) for admin_id in group_doc["group_admins"]]
            group_admins = list(
                flask_mongo.db.users.find(
                    {"_id": {"$in": admin_ids}}, {"_id": 1, "display_name": 1, "contact_email": 1}
                )
            )
            group_data["group_admins"] = [
                {
                    "immutable_id": str(admin["_id"]),
                    "display_name": admin.get("display_name", ""),
                    "contact_email": admin.get("contact_email", ""),
                }
                for admin in group_admins
            ]

        groups_data.append(group_data)

    return jsonify(
        {
            "status": "success",
            "data": groups_data,
        }
    ), 200


@ADMIN.route("/groups", methods=["PUT"])
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


@ADMIN.route("/groups", methods=["DELETE"])
def delete_group():
    request_json = request.get_json()

    group_id = request_json.get("immutable_id")
    if group_id is not None:
        result = flask_mongo.db.groups.delete_one({"_id": ObjectId(group_id)})

        if result.deleted_count == 1:
            return jsonify({"status": "success"}), 200

    return jsonify({"status": "error", "message": "Unable to delete group."}), 400


@ADMIN.route("/groups/<group_immutable_id>", methods=["PUT"])
def update_group(group_immutable_id):
    request_json = request.get_json()

    existing_group = flask_mongo.db.groups.find_one({"_id": ObjectId(group_immutable_id)})
    if not existing_group:
        return jsonify({"status": "error", "message": "Group not found."}), 404

    update_data = {}

    if "display_name" in request_json:
        update_data["display_name"] = request_json["display_name"]

    if "description" in request_json:
        update_data["description"] = request_json["description"]

    if "group_admins" in request_json:
        update_data["group_admins"] = request_json["group_admins"]

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


@ADMIN.route("/groups/<group_immutable_id>", methods=["PATCH"])
def add_user_to_group(group_immutable_id):
    request_json = request.get_json()
    user_id = request_json.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "No user ID provided."}), 400

    group_exists = flask_mongo.db.groups.find_one({"_id": ObjectId(group_immutable_id)})
    if not group_exists:
        return jsonify({"status": "error", "message": "Group does not exist."}), 400

    update_user = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"group_ids": ObjectId(group_immutable_id)}},
    )

    if update_user.modified_count == 1:
        return jsonify({"status": "success", "message": "User added to group successfully."}), 200
    else:
        return jsonify({"status": "error", "message": "Unable to add user to group."}), 400
