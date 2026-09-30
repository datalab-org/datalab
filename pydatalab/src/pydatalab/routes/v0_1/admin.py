import datetime
import secrets

import pymongo.errors
from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest, Conflict, NotFound

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models.people import AccountStatus, Group, Person
from pydatalab.mongo import flask_mongo, gravatar_hash_for
from pydatalab.permissions import admin_only


def check_manager_cycle(user_id: ObjectId, new_manager_id: ObjectId) -> bool:
    """Query the database to check if assigning new_manager_id as a manager
    causes any cyclic management relationships with user_id.

    Parameters:
        user_id: The ObjectId of the user being assigned a new manager.
        new_manager_id: The ObjectId of the proposed new manager.

    Returns:
        True if a cycle is detected, False otherwise.

    """
    visited: set[ObjectId] = set()
    user_id = ObjectId(user_id)

    max_depth: int = 10
    depth: int = 0
    ids_to_check: set[ObjectId] = {ObjectId(new_manager_id)}

    # Loop through the management hierarchy; after looping, if the `user_id` is found listed as a manager
    # of any "parents", then we have a cycle
    while ids_to_check and depth <= max_depth:
        # If we have found the user as another manager in the hierarchy, we have a cycle
        if user_id in ids_to_check:
            return True

        depth += 1

        # Otherwise descend further and look at previous managers of managers
        ids_to_check -= visited
        next_ids_to_check = set()

        for _id in ids_to_check:
            manager = flask_mongo.db.users.find_one({"_id": _id}, projection={"managers": 1})
            visited.add(_id)
            if manager and manager.get("managers", []):
                for m in manager["managers"]:
                    next_ids_to_check.add(ObjectId(m))

        if next_ids_to_check:
            ids_to_check = ids_to_check.union(next_ids_to_check)

    if depth > max_depth:
        raise RuntimeError(
            "Maximum management hierarchy depth exceeded indicating malformed user database; possible cycle detected but not proceeding further"
        )

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
                    # Users store groups as [{immutable_id: ObjectId}] subdocuments (unlike items which use a flat group_ids list),
                    # so $map is needed to extract the ObjectIds before $in can match against groups._id.
                    "let": {
                        "group_ids": {
                            "$map": {
                                "input": {"$ifNull": ["$groups", []]},
                                "as": "g",
                                "in": "$$g.immutable_id",
                            }
                        }
                    },
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", "$$group_ids"]}}},
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

    return jsonify({"status": "success", "data": [Person(**d).model_dump() for d in users_list]})


@ADMIN.route("/roles/<user_id>", methods=["PATCH"])
def save_role(user_id):
    request_json = request.get_json()

    if request_json is not None:
        user_role = request_json

    if not current_user.is_authenticated:
        return (jsonify({"status": "error", "message": "No user authenticated."}), 401)

    if current_user.role != "admin":
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

            manager_object_ids.append(manager_oid)

    update_result = flask_mongo.db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"managers": manager_object_ids}}
    )

    if update_result.matched_count != 1:
        return jsonify({"status": "error", "message": "Unable to update user managers"}), 400

    return jsonify({"status": "success"}), 200


def _find_user_references(user_id: ObjectId) -> dict[str, int]:
    """Count the documents in other collections that refer to this user
    as a creator or author, i.e., those that would be left dangling if
    the user was removed from the database entirely.

    """
    db = flask_mongo.db
    references = {
        "items": db.items.count_documents({"creator_ids": user_id}),
        "collections": db.collections.count_documents({"creator_ids": user_id}),
        "files": db.files.count_documents({"creator_ids": user_id}),
        "item_versions": db.item_versions.count_documents({"user_id": user_id}),
        "block_versions": db.block_versions.count_documents({"user_id": user_id}),
        "tasks": db.tasks.count_documents({"creator_id": user_id}),
    }
    return {k: v for k, v in references.items() if v}


def _remove_user_credentials_and_memberships(user_id: ObjectId, emails: set[str]) -> None:
    """Remove all ways in which this user could authenticate, and remove them from
    any management roles over other users and groups.

    Access tokens created by the user for sharing specific items are retained,
    as these belong to the shared item rather than the user; they can be
    revoked separately.

    """
    db = flask_mongo.db
    db.api_keys.delete_many({"user": user_id, "type": "api_key"})
    # Legacy API keys are keyed by the user ID
    db.api_keys.delete_many({"_id": user_id, "type": {"$exists": False}})
    if emails:
        db.magic_links.delete_many({"email": {"$in": list(emails)}})
    db.users.update_many({"managers": user_id}, {"$pull": {"managers": user_id}})
    db.groups.update_many({"managers": user_id}, {"$pull": {"managers": user_id}})


@ADMIN.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id: str):
    """Irreversibly delete a user account and all of their personal data.

    **This is a destructive operation that cannot be undone from within datalab.**
    Note that the removed data will likely persist in any database backups until
    those backups expire, so that it can still be recovered if a restore is required.

    By default, the account is "tombstoned": the user document is retained, so that
    anything the user created (items, collections, files, versions) remains intact
    and correctly attributed, but all of their identities, email addresses, API keys
    and management roles are removed, and their display name is replaced with a random
    pseudonym. The account status is set to `deleted`, which prevents it from ever being
    used to log in again. If the same person logs in again with a previously connected
    identity, a new, empty account will be created.

    If the `expunge` query parameter is set to true, the user document will instead be
    removed from the database entirely, e.g., for accounts registered without
    authorisation. This is only allowed if nothing else in the database refers to the
    user; otherwise, a 409 Conflict response is returned listing the references.

    """
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise BadRequest(f"Invalid user ID: {user_id}")

    if str(user_oid) == str(current_user.id):
        raise BadRequest("Admins cannot delete their own account.")

    user = flask_mongo.db.users.find_one({"_id": user_oid})
    if not user:
        raise NotFound("User not found.")

    expunge = request.args.get("expunge", "false").lower() in ("1", "true", "yes")

    emails = {
        identity["identifier"]
        for identity in user.get("identities") or []
        if identity.get("identity_type") == "email" and identity.get("identifier")
    }
    if user.get("contact_email"):
        emails.add(user["contact_email"])

    if expunge:
        references = _find_user_references(user_oid)
        if references:
            raise Conflict(
                "Cannot expunge user as other entries refer to them "
                f"({', '.join(f'{k}: {v}' for k, v in references.items())}); "
                "delete the account without expunging to retain these entries instead."
            )
        _remove_user_credentials_and_memberships(user_oid, emails)
        flask_mongo.db.roles.delete_one({"_id": user_oid})
        flask_mongo.db.users.delete_one({"_id": user_oid})
        LOGGER.warning("User %s expunged by admin %s", user_oid, current_user.id)
        return jsonify({"status": "success", "message": "User account expunged."}), 200

    if user.get("account_status") == AccountStatus.DELETED:
        return jsonify({"status": "success", "message": "User account already deleted."}), 200

    display_name = f"{secrets.token_hex(3)} (deleted user)"
    _remove_user_credentials_and_memberships(user_oid, emails)
    flask_mongo.db.users.update_one(
        {"_id": user_oid},
        {
            "$set": {
                "contact_email": None,
                "display_name": display_name,
                "gravatar_hash": gravatar_hash_for(None, display_name),
                "groups": [],
                "managers": [],
                "account_status": AccountStatus.DELETED,
            },
            # Unset rather than empty the identities, as an empty list is indexed as
            # null by the unique identities index, which would only allow one such user
            "$unset": {"identities": ""},
        },
    )
    LOGGER.warning("User %s deleted by admin %s", user_oid, current_user.id)

    return jsonify(
        {"status": "success", "message": "User account deleted.", "display_name": display_name}
    ), 200


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
                    "gravatar_hash": 1,
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
                    "gravatar_hash": 1,
                }
            },
        ],
        "as": "managers",
    }

    group_docs = flask_mongo.db.groups.aggregate(
        [{"$match": {}}, {"$lookup": members_lookup}, {"$lookup": managers_lookup}]
    )

    return jsonify(
        {"status": "success", "data": [Group(**d).model_dump() for d in group_docs]}
    ), 200


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
            group.model_dump(exclude_unset=True)
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
