from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.mongo import flask_mongo

user = Blueprint("users", __name__)


@user.route("/users/<user_id>", methods=["PATCH"])
def save_user(user_id):
    request_json = request.get_json()

    display_name = request_json.get("display_name")
    contact_email = request_json.get("contact_email")

    if not current_user.is_authenticated:
        return jsonify(status="error"), 401

    if current_user.id != user_id and current_user.role != "admin":
        return jsonify(status="error"), 403

    update_result = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"display_name": display_name, "contact_email": contact_email}},
    )

    if update_result.modified_count != 1:
        return jsonify(
            status="error",
            detail="Unable to update {user_id=}.",
        ), 400

    return jsonify(status="success"), 200
