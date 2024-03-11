from bson import ObjectId
from flask import Blueprint, jsonify, request

from pydatalab.mongo import flask_mongo

user = Blueprint("users", __name__)


@user.route("/users/<user_id>", methods=["PATCH"])
def save_user(user_id):
    user_name = request.json.get("data", {}).get("user_name")

    user_id_object = ObjectId(user_id)
    update_result = flask_mongo.db.users.update_one(
        {"_id": user_id_object}, {"$set": {"display_name": user_name}}
    )
    if update_result.nmodified != 1:
        return jsonify(
            status="error",
            detail="User does not have the appropriate permissions to update the given user ID.",
        ), 403

    return jsonify(status="success"), 200
