import json

import pymongo.errors
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.people import Group, User
from pydatalab.mongo import _get_active_mongo_client, flask_mongo
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


@ADMIN.route("/groups", methods=["GET"])
def get_groups():
    return jsonify(
        {
            "status": "success",
            "data": [json.loads(Group(**d).json()) for d in flask_mongo.db.groups.find()],
        }
    ), 200


@ADMIN.route("/groups", methods=["PUT"])
@admin_only
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


@ADMIN.route("/groups/<group_immutable_id>", methods=["PATCH"])
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
