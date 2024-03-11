from bson import ObjectId
from flask import Blueprint, jsonify, request

from flask_login import current_user

from pydatalab.mongo import flask_mongo


user = Blueprint("users", __name__)


@user.route("/users/<user_id>", methods=["PATCH"])
def save_user(user_id):
    user_name = request.json.get("data", {}).get("user_name")

    if not current_user.authenticated:
        return jsonify(status="error"), 401

    if current_user.id != user_id and current_user.role != "admin":
        return jsonify(status="error"), 403

    update_result = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"display_name": user_name}})
    if update_result.nmodified != 1:
        return jsonify(status="error", detail="User does not have the appropriate permissions to update the given user ID."), 403

    return jsonify(status="success"), 200
