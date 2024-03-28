from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.mongo import flask_mongo

role = Blueprint("roles", __name__)


@role.route("/roles/<user_id>", methods=["PATCH"])
def save_role(user_id):
    request_json = request.get_json()

    user_role: str

    if request_json is not None:
        user_role = request_json

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (jsonify({"status": "error", "message": "No user authenticated."}), 401)

    if not CONFIG.TESTING and current_user.role != "admin":
        return (
            jsonify({"status": "error", "message": "User not allowed to edit this profile."}),
            403,
        )

    existing_user = flask_mongo.db.roles.find_one({"_id": ObjectId(user_id)})

    if not existing_user:
        if not user_role:
            return (jsonify({"status": "error", "message": "Role not provided for new user."}), 400)

        new_user_role = {"_id": ObjectId(user_id), "role": user_role}
        flask_mongo.db.roles.insert_one(new_user_role)

        return (jsonify({"status": "success", "message": "New user's role created."}), 201)

    update_result = flask_mongo.db.roles.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"role": user_role}}
    )

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
