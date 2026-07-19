import datetime
import json

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from pydatalab.feature_flags import FEATURE_FLAGS
from pydatalab.logger import logged_route
from pydatalab.models.tags import Tag
from pydatalab.mongo import (
    TAGS_FTS_FIELDS,
    build_search_pipeline,
    flask_mongo,
    insert_pydantic_model_fork_safe,
)
from pydatalab.permissions import active_users_or_get_only, admin_only

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


def _name_conflict_exists(name: str, exclude_id: ObjectId | None = None) -> bool:
    """Whether a (global) tag with `name` already exists.

    All tags are global, so names are unique across the whole collection.
    `immutable_id` remains the true identity, so references never break on rename.
    """
    query: dict = {"name": name}
    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}

    return flask_mongo.db.tags.find_one(query, {"_id": 1}) is not None


@TAGS.route("/tags", methods=["PUT"])
@admin_only
def create_tag():
    """Create a new global tag. Restricted to administrators."""
    request_json = request.get_json()
    data = request_json.get("data", {})

    name = data.get("name")
    if not name:
        return jsonify(status="error", message="A tag name is required."), 400

    if _name_conflict_exists(name):
        return (
            jsonify(status="error", message=f"A tag named {name!r} already exists."),
            409,  # 409: Conflict
        )

    try:
        tag = Tag(
            name=name,
            description=data.get("description"),
            color=data.get("color"),
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
    """Return all (global) tags, readable by any user."""
    tags = flask_mongo.db.tags.find({}).sort("name", 1)
    data = [Tag(**doc).model_dump(mode="json") for doc in tags]
    return jsonify({"status": "success", "data": data})


@TAGS.route("/search-tags", methods=["GET"])
def search_tags():
    """Perform a full-text search over all tags.

    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of results (default 100).

    Returns:
        A list of `{type, immutable_id, name, description, color}` dictionaries in
        order of descending match score, suitable for use as tag references.
    """
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)

    if not query:
        return jsonify({"status": "error", "message": "No query provided."}), 400

    pipeline = build_search_pipeline(query, TAGS_FTS_FIELDS, None)
    pipeline.append({"$limit": nresults})
    pipeline.append({"$project": {"_id": 1, "name": 1, "description": 1, "color": 1}})

    data = [
        {
            "type": "tags",
            "immutable_id": str(doc["_id"]),
            "name": doc.get("name"),
            "description": doc.get("description"),
            "color": doc.get("color"),
        }
        for doc in flask_mongo.db.tags.aggregate(pipeline)
    ]

    return jsonify({"status": "success", "data": data}), 200


@TAGS.route("/tags/<tag_id>", methods=["PATCH"])
@admin_only
@logged_route
def save_tag(tag_id):
    """Update a tag's `name`/`description`/`color`. Restricted to administrators."""
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

    # Identity is not editable through this endpoint.
    for key in ("_id", "immutable_id", "type"):
        updated_data.pop(key, None)

    updated_data["last_modified"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    tag = flask_mongo.db.tags.find_one({"_id": object_id})

    if not tag:
        return (
            jsonify(status="error", message=f"Unable to find a tag with ID {tag_id!r}."),
            400,
        )

    # Keep names globally unique on rename.
    if "name" in updated_data and _name_conflict_exists(updated_data["name"], exclude_id=object_id):
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
@admin_only
def delete_tag(tag_id: str):
    """Delete a tag and drop its references from items. Restricted to administrators."""
    object_id = _parse_object_id(tag_id)
    if object_id is None:
        return jsonify(status="error", message=f"Invalid tag ID {tag_id!r}."), 400

    result = flask_mongo.db.tags.delete_one({"_id": object_id})

    if result.deleted_count != 1:
        return (
            jsonify(status="error", message=f"No tag found with ID {tag_id!r}."),
            404,
        )

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
