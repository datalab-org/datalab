from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.people import Group, Person
from pydatalab.mongo import flask_mongo

user = Blueprint("users", __name__)


@user.route("/users/<user_id>", methods=["PATCH"])
def save_user(user_id):
    request_json = request.get_json()

    display_name = request_json.get("display_name", False)
    contact_email = request_json.get("contact_email", False)

    if not current_user.is_authenticated:
        return jsonify(status="error"), 401

    if current_user.id != user_id and current_user.role != "admin":
        return jsonify(status="error"), 403

    update = {}

    if contact_email or contact_email in (None, ""):
        if contact_email == "":
            contact_email = None
        update["contact_email"] = contact_email

    if display_name:
        update["display_name"] = display_name

    if not update:
        return jsonify(status="success", detail="No update was performed."), 200

    update_result = flask_mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})

    if update_result.matched_count != 1:
        return jsonify(status="error", detail="Unable to update user."), 400

    if update_result.modified_count != 1:
        return jsonify(
            status="success",
            detail="No update was performed",
        ), 200

    return jsonify(status="success"), 200


@user.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    if not current_user.is_authenticated or not CONFIG.TESTING:
        return jsonify(status="error"), 401

    # if current_user.id != user_id and current_user.role != "admin":
    #     return jsonify(status="error"), 403

    user = flask_mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if user:
        roles = flask_mongo.db.roles.find_one({"_id": ObjectId(user_id)})

        groups = []
        if user.get("groups", []):
            groups = flask_mongo.db.groups.find(
                {"_id": {"$in": [ObjectId(g) for g in user.get("groups", [])]}}
            )

        user = Person(**user).dict()
        user["roles"] = roles
        user["groups"] = groups
        return jsonify(user), 200

    return jsonify(status="error", detail="User not found."), 404


@user.route("/groups", methods=["POST"])
def create_group():
    request_json = request.get_json()

    if not current_user.is_authenticated or not CONFIG.TESTING:
        return jsonify(status="error", detail="You must be logged in to create a group."), 403

    data = request_json.get("data", {})
    starting_members = data.pop("starting_members", [])

    if not data:
        return jsonify(status="error", detail="No data provided."), 400

    group = Group(**data)
    group_immutable_id = flask_mongo.db.groups.insert_one(group.dict()).inserted_id

    for member in starting_members:
        flask_mongo.db.users.update_one(
            {"_id": ObjectId(member)}, {"$push": {"groups": group_immutable_id}}
        )

    return jsonify(status="success"), 200
