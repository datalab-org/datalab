import datetime
import json

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, abort, jsonify, request
from flask_login import current_user
from pydantic import ValidationError

from pydatalab.feature_flags import FEATURE_FLAGS
from pydatalab.logger import logged_route
from pydatalab.models.tags import Tag
from pydatalab.models.utils import AccessScope, UserRole
from pydatalab.mongo import (
    TAGS_FTS_FIELDS,
    build_search_pipeline,
    flask_mongo,
    insert_pydantic_model_fork_safe,
)
from pydatalab.permissions import active_users_or_get_only

TAGS = Blueprint("tags", __name__)


@TAGS.before_request
def _require_tags_feature():
    """Gate the whole blueprint behind the `tags` feature flag."""
    if not FEATURE_FLAGS.tags:
        abort(404)


@TAGS.before_request
@active_users_or_get_only
def _(): ...


def _parse_object_id(raw: str) -> ObjectId | None:
    """Parse a string into an ObjectId, returning None if it is not valid."""
    try:
        return ObjectId(raw)
    except (InvalidId, TypeError):
        return None


def _is_admin() -> bool:
    """Whether the current user is an authenticated administrator."""
    return bool(current_user.is_authenticated and current_user.role == UserRole.ADMIN)


def _current_user_id() -> ObjectId | None:
    """The immutable ID of the current user, or None if unauthenticated."""
    if current_user.is_authenticated and current_user.person is not None:
        return current_user.person.immutable_id
    return None


def _usable_tags_filter(user_id: ObjectId | None) -> dict:
    """The Mongo filter for tags the given user may list and use.

    This is global tags plus the user's own personal tags.
    """
    if user_id is None:
        return {"scope": AccessScope.GLOBAL.value}
    return {"$or": [{"scope": AccessScope.GLOBAL.value}, {"owner": user_id}]}


def _name_conflict_exists(
    name: str,
    scope: AccessScope,
    owner: ObjectId | None = None,
    exclude_id: ObjectId | None = None,
) -> bool:
    """Whether a tag with `name` already exists within the given scope.

    The same name may exist across scopes (e.g. a global `x` and a personal `x`).
    """
    query: dict = {"name": name, "scope": scope.value}
    if scope == AccessScope.USER:
        query["owner"] = owner

    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}

    return flask_mongo.db.tags.find_one(query, {"_id": 1}) is not None


def _authorize_tag_write(tag_doc: dict) -> bool:
    """Whether the current user may edit or delete the given tag document.

    Global tags require an administrator; personal tags require the owner.
    """
    if tag_doc["scope"] == AccessScope.USER.value:
        user_id = _current_user_id()
        return user_id is not None and tag_doc.get("owner") == user_id
    return _is_admin()


@TAGS.route("/tags", methods=["PUT"])
def create_tag():
    """Create a new tag.

    Anyone logged in can create a personal tag. Only administrators can create
    global tags.
    """
    request_json = request.get_json()
    data = request_json.get("data", {})

    name = data.get("name")
    if not name:
        return jsonify(status="error", message="A tag name is required."), 400

    try:
        scope = AccessScope(data.get("scope") or AccessScope.USER.value)
    except ValueError:
        return (
            jsonify(status="error", message=f"Invalid tag scope {data.get('scope')!r}."),
            400,
        )

    if scope == AccessScope.GLOBAL:
        if not _is_admin():
            return (
                jsonify(status="error", message="Only administrators can create global tags."),
                403,
            )
        owner = None
    else:
        owner = _current_user_id()
        if owner is None:
            return (
                jsonify(status="error", message="You must be logged in to create a personal tag."),
                401,
            )

    if _name_conflict_exists(name, scope, owner):
        return (
            jsonify(status="error", message=f"A tag named {name!r} already exists."),
            409,  # 409: Conflict
        )

    try:
        tag = Tag(
            name=name,
            description=data.get("description"),
            color=data.get("color"),
            scope=scope,
            owner=owner,
            last_modified=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
    except ValidationError as error:
        return (
            jsonify(status="error", message="Unable to create the tag.", output=str(error)),
            400,
        )

    tag.immutable_id = insert_pydantic_model_fork_safe(tag, "tags")

    return jsonify({"status": "success", "data": json.loads(tag.model_dump_json())}), 201


@TAGS.route("/tags", methods=["GET"])
def get_tags():
    """Return the tags usable by the current user: global tags plus their own."""
    tags = flask_mongo.db.tags.find(_usable_tags_filter(_current_user_id())).sort("name", 1)
    data = [Tag(**doc).model_dump(mode="json") for doc in tags]
    return jsonify({"status": "success", "data": data})


@TAGS.route("/search-tags", methods=["GET"])
def search_tags():
    """Perform a full-text search over the tags usable by the current user.

    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of results (default 100).

    Returns:
        A list of `{type, immutable_id, name, description, color, scope}`
        dictionaries in order of descending match score, suitable for use as tag
        references.
    """
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)

    if not query:
        return jsonify({"status": "error", "message": "No query provided."}), 400

    pipeline = build_search_pipeline(
        query, TAGS_FTS_FIELDS, _usable_tags_filter(_current_user_id())
    )
    pipeline.append({"$limit": nresults})
    pipeline.append({"$project": {"_id": 1, "name": 1, "description": 1, "color": 1, "scope": 1}})

    data = [
        {
            "type": "tags",
            "immutable_id": str(doc["_id"]),
            "name": doc.get("name"),
            "description": doc.get("description"),
            "color": doc.get("color"),
            "scope": doc["scope"],
        }
        for doc in flask_mongo.db.tags.aggregate(pipeline)
    ]

    return jsonify({"status": "success", "data": data}), 200


@TAGS.route("/tags/<tag_id>", methods=["PATCH"])
@logged_route
def save_tag(tag_id):
    """Update a tag's `name`/`description`/`color`.

    Global tags may only be edited by administrators; personal tags only by their
    owner.
    """
    object_id = _parse_object_id(tag_id)
    if object_id is None:
        return jsonify(status="error", message=f"Invalid tag ID {tag_id!r}."), 400

    request_json = request.get_json()
    updated_data = request_json.get("data")

    if not updated_data:
        return (
            jsonify(status="error", message="No data provided to update the tag with."),
            400,  # 400: Bad Request
        )

    tag = flask_mongo.db.tags.find_one({"_id": object_id})

    if not tag:
        return (
            jsonify(status="error", message=f"Unable to find a tag with ID {tag_id!r}."),
            404,
        )

    if not _authorize_tag_write(tag):
        return (
            jsonify(status="error", message="You are not allowed to modify this tag."),
            403,
        )

    # Identity, scope and ownership are not editable through this endpoint.
    for key in ("_id", "immutable_id", "type", "scope", "owner"):
        updated_data.pop(key, None)

    updated_data["last_modified"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Keep names unique within the tag's own scope on rename.
    if "name" in updated_data:
        scope = AccessScope(tag["scope"])
        if _name_conflict_exists(
            updated_data["name"], scope, tag.get("owner"), exclude_id=object_id
        ):
            return (
                jsonify(
                    status="error",
                    message=f"A tag named {updated_data['name']!r} already exists.",
                ),
                409,
            )

    tag.update(updated_data)

    try:
        tag = Tag(**tag).model_dump(exclude={"immutable_id"})
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update tag {tag_id!r} with new data {updated_data}.",
                output=str(exc),
            ),
            400,
        )

    result = flask_mongo.db.tags.update_one({"_id": object_id}, {"$set": tag})

    if result.modified_count != 1:
        return (
            jsonify(
                status="error",
                message=f"Unable to update tag {tag_id!r}.",
                output=result.raw_result,
            ),
            400,
        )

    return jsonify(status="success"), 200


@TAGS.route("/tags/<tag_id>", methods=["DELETE"])
def delete_tag(tag_id: str):
    """Delete a tag and drop its references from items.

    Global tags may only be deleted by administrators; personal tags only by
    their owner.
    """
    object_id = _parse_object_id(tag_id)
    if object_id is None:
        return jsonify(status="error", message=f"Invalid tag ID {tag_id!r}."), 400

    tag = flask_mongo.db.tags.find_one({"_id": object_id})

    if not tag:
        return (
            jsonify(status="error", message=f"No tag found with ID {tag_id!r}."),
            404,
        )

    if not _authorize_tag_write(tag):
        return (
            jsonify(status="error", message="You are not allowed to delete this tag."),
            403,
        )

    flask_mongo.db.tags.delete_one({"_id": object_id})

    # Best-effort cleanup: drop references to the deleted tag from items' `tags`
    # arrays. Like collection deletion, this is a raw update that does NOT go
    # through the item save route, so it neither bumps `last_modified` nor creates
    # a new item version.
    #
    # This hardcodes `items` as the only `HasTags` collection. Extend it if
    # `HasTags` is applied to other entities. Note that references are not deleted
    # from item_versions, so a reference to a deleted tag can survive there.
    flask_mongo.db.items.update_many(
        {"tags": {"$elemMatch": {"immutable_id": object_id, "type": "tags"}}},
        {"$pull": {"tags": {"immutable_id": object_id, "type": "tags"}}},
    )

    return jsonify(status="success"), 200
