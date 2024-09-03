from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG, BackupHealthCheck
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import admin_only, get_default_permissions

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
                    }
                }
            },
        ]
    )

    return jsonify({"status": "success", "data": list(users)})


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


@ADMIN.route("/health/backups")
def check_backup_health():
    """Loop over all backup strategies and provide information on their health,
    and provide download links.

    """
    results = {}

    if not CONFIG.BACKUP_STRATEGIES:
        return jsonify({"status": "success", "message": "No backup strategies configured."}), 204

    for strat_name, strat in CONFIG.BACKUP_STRATEGIES.items():
        results[strat_name] = BackupHealthCheck(strat.healthcheck())

    response = {"status": "success", "data": results}

    return jsonify(response), 200
