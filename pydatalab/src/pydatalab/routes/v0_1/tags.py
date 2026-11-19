import datetime
import json

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, NotFound, Unauthorized

from pydatalab.feature_flags import FEATURE_FLAGS
from pydatalab.logger import logged_route
from pydatalab.models.tags import Tag, TagAccessScope
from pydatalab.mongo import (
    TAGS_FTS_FIELDS,
    build_search_pipeline,
    flask_mongo,
    inline_tag_owner_display,
    insert_pydantic_model_fork_safe,
)
from pydatalab.permissions import (
    active_users_or_get_only,
    current_user_group_ids,
    current_user_id,
    get_managed_group_ids,
    is_admin,
    is_group_manager,
)
from pydatalab.tags import (
    can_manage_tag,
    delete_tags_and_references,
    get_listable_tags_filter,
    get_usable_tags_filter,
)

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


def _name_conflict_exists(
    name: str,
    scope: TagAccessScope,
    owner: ObjectId | None = None,
    exclude_id: ObjectId | None = None,
) -> bool:
    """Whether a tag with `name` already exists within the given scope.

    The same name may exist across scopes (e.g. a global `x` and a user-defined `x`),
    and across owners within the user and group scopes.
    """
    query: dict = {"name": name, "scope": scope.value}
    if scope in (TagAccessScope.USER, TagAccessScope.GROUP):
        query["owner"] = owner

    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}

    return flask_mongo.db.tags.find_one(query, {"_id": 1}) is not None


def _resolve_group_tag_owner(raw_owner) -> ObjectId:
    """Validate the owning group requested for a group tag and check that the current
    user may create tags for it (an administrator or one of its managers).
    """
    group_id = _parse_object_id(raw_owner) if isinstance(raw_owner, str) else None
    if group_id is None:
        raise BadRequest("A group tag requires the ID of its group as `owner`.")

    if flask_mongo.db.groups.find_one({"_id": group_id}, {"_id": 1}) is None:
        raise BadRequest(f"No group found with ID {raw_owner!r}.")

    if not (is_admin() or is_group_manager(group_id, current_user_id())):
        raise Forbidden("Only administrators and the group's managers can create group tags.")

    return group_id


@TAGS.route("/tags", methods=["PUT"])
def create_tag():
    """Create a new tag.

    Anyone logged in can create a user-defined tag. Only administrators can create
    global tags. Group tags can be created by administrators and by the managers of
    the group, whose ID must be given as `owner`.

    The returned tag carries `can_manage` (always true for its creator) and, for user
    and group tags, the `owner_name` of the owning user or group.
    """
    request_json = request.get_json()
    data = request_json.get("data", {})

    name = data.get("name")
    if not name:
        raise BadRequest("A tag name is required.")

    try:
        scope = TagAccessScope(data.get("scope") or TagAccessScope.USER.value)
    except ValueError:
        raise BadRequest(f"Invalid tag scope {data.get('scope')!r}.")

    if scope == TagAccessScope.GLOBAL:
        if not is_admin():
            raise Forbidden("Only administrators can create global tags.")
        owner = None
    elif scope == TagAccessScope.GROUP:
        if current_user_id() is None:
            raise Unauthorized("You must be logged in to create a group tag.")
        owner = _resolve_group_tag_owner(data.get("owner"))
    else:
        owner = current_user_id()
        if owner is None:
            raise Unauthorized("You must be logged in to create a user-defined tag.")

    if _name_conflict_exists(name, scope, owner):
        raise Conflict(f"A tag named {name!r} already exists.")

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
        raise BadRequest(f"Unable to create the tag: {error}")

    tag.immutable_id = insert_pydantic_model_fork_safe(tag, "tags")

    data = json.loads(tag.model_dump_json())
    data["can_manage"] = True
    inline_tag_owner_display([data])

    return jsonify({"status": "success", "data": data}), 201


@TAGS.route("/tags", methods=["GET"])
def get_tags():
    """Return the tags the current user may list.

    These are the tags they may use (global tags, their own user-defined tags and the
    tags of the groups they belong to) plus the group tags they may manage without
    being a member (those of the groups they manage, or all of them for
    administrators). Administrators in super-user mode (`?sudo=1`) get all tags.

    Each tag carries `can_manage` (whether the current user may edit and delete it)
    and, for user and group tags, the `owner_name` of the owning user or group.
    """
    managed_group_ids = get_managed_group_ids(current_user_id())
    tags = flask_mongo.db.tags.find(get_listable_tags_filter(managed_group_ids)).sort("name", 1)

    data = []
    for doc in tags:
        tag = Tag(**doc).model_dump(mode="json")
        tag["can_manage"] = can_manage_tag(doc, managed_group_ids)
        data.append(tag)
    inline_tag_owner_display(data)

    return jsonify({"status": "success", "data": data})


@TAGS.route("/tags/manageable-groups", methods=["GET"])
def get_manageable_tag_groups():
    """Return the groups the current user may create group tags for: the groups they
    manage, or all groups for administrators.
    """
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"status": "success", "data": []})

    query = {} if is_admin() else {"managers": user_id}
    groups = flask_mongo.db.groups.find(
        query, projection={"_id": 1, "display_name": 1, "group_id": 1}
    ).sort("display_name", 1)

    data = [
        {
            "immutable_id": str(group["_id"]),
            "display_name": group.get("display_name"),
            "group_id": group.get("group_id"),
        }
        for group in groups
    ]
    return jsonify({"status": "success", "data": data})


@TAGS.route("/search-tags", methods=["GET"])
def search_tags():
    """Perform a full-text search over the tags usable by the current user.

    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of results (default 100).

    Returns:
        A list of `{type, immutable_id, name, description, color, scope}`
        dictionaries (plus `owner_name` for user and group tags) in order of descending match
        score, suitable for use as tag references.
    """
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)

    if not query:
        raise BadRequest("No query provided.")

    pipeline = build_search_pipeline(
        query,
        TAGS_FTS_FIELDS,
        get_usable_tags_filter(current_user_id(), current_user_group_ids()),
    )
    pipeline.append({"$limit": nresults})
    pipeline.append(
        {"$project": {"_id": 1, "name": 1, "description": 1, "color": 1, "scope": 1, "owner": 1}}
    )

    docs = list(flask_mongo.db.tags.aggregate(pipeline))
    inline_tag_owner_display(docs)

    data = []
    for doc in docs:
        result = {
            "type": "tags",
            "immutable_id": str(doc["_id"]),
            "name": doc.get("name"),
            "description": doc.get("description"),
            "color": doc.get("color"),
            "scope": doc["scope"],
        }
        if "owner_name" in doc:
            result["owner_name"] = doc["owner_name"]
        data.append(result)

    return jsonify({"status": "success", "data": data}), 200


def _requested_scope_change(tag: dict, data: dict) -> tuple[TagAccessScope, ObjectId | None] | None:
    """The new `(scope, owner)` requested for an existing tag by `data`, or None if
    `data` does not change them.

    A tag can be moved to the global scope or to a group (whose ID is given as `owner`),
    but not to the user scope. Raises `BadRequest` for an invalid target.
    """
    if "scope" not in data:
        return None

    try:
        scope = TagAccessScope(data["scope"])
    except ValueError:
        raise BadRequest(f"Invalid tag scope {data['scope']!r}.")

    if scope.value == tag["scope"]:
        if scope != TagAccessScope.GROUP:
            return None
        # Same scope: only moving a group tag to another group is a change.
        raw_owner = data.get("owner")
        if raw_owner is None or str(raw_owner) == str(tag.get("owner")):
            return None

    if scope == TagAccessScope.USER:
        raise BadRequest("A tag cannot be moved to the user scope.")

    owner = None if scope == TagAccessScope.GLOBAL else _resolve_group_tag_owner(data.get("owner"))
    return scope, owner


@TAGS.route("/tags/<tag_id>", methods=["PATCH"])
@logged_route
def save_tag(tag_id):
    """Update a tag's `name`/`description`/`color` and, for administrators, its scope.

    Administrators may edit any tag; otherwise, user-defined tags may only be edited by
    their owner and group tags by the group's managers.

    Administrators can also change the tag's scope by giving `scope` (`"global"` or
    `"group"`) and, for group tags, the group's immutable ID as `owner`, e.g. to promote
    a user-defined tag. Tags cannot be moved to the user scope. Items reference tags by
    ID, so tagged items keep the tag. The tag's name must not clash with another tag in
    the target scope.
    """
    object_id = _parse_object_id(tag_id)
    if object_id is None:
        raise BadRequest(f"Invalid tag ID {tag_id!r}.")

    request_json = request.get_json()
    updated_data = request_json.get("data")

    if not updated_data:
        raise BadRequest("No data provided to update the tag with.")

    tag = flask_mongo.db.tags.find_one({"_id": object_id})

    if not tag:
        raise NotFound(f"Unable to find a tag with ID {tag_id!r}.")

    if not can_manage_tag(tag, get_managed_group_ids(current_user_id())):
        raise Forbidden("You are not allowed to modify this tag.")

    # Only administrators can change the scope and ownership.
    scope_change = _requested_scope_change(tag, updated_data)
    if scope_change is not None and not is_admin():
        raise Forbidden("Only administrators can change the scope of a tag.")

    # Identity is not editable; scope and ownership are only set from `scope_change`.
    for key in ("_id", "immutable_id", "type", "scope", "owner"):
        updated_data.pop(key, None)

    if scope_change is not None:
        updated_data["scope"], updated_data["owner"] = scope_change

    updated_data["last_modified"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Keep names unique within the tag's (possibly new) scope on rename or scope change.
    if "name" in updated_data or scope_change is not None:
        name = updated_data.get("name", tag["name"])
        scope = TagAccessScope(updated_data.get("scope", tag["scope"]))
        owner = updated_data["owner"] if "owner" in updated_data else tag.get("owner")
        if _name_conflict_exists(name, scope, owner, exclude_id=object_id):
            raise Conflict(f"A tag named {name!r} already exists.")

    tag.update(updated_data)

    try:
        tag = Tag(**tag).model_dump(exclude={"immutable_id"})
    except ValidationError as exc:
        raise BadRequest(f"Unable to update tag {tag_id!r} with new data {updated_data}: {exc}")

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

    Administrators may delete any tag; otherwise, user-defined tags may only be
    deleted by their owner and group tags by the group's managers.
    """
    object_id = _parse_object_id(tag_id)
    if object_id is None:
        raise BadRequest(f"Invalid tag ID {tag_id!r}.")

    tag = flask_mongo.db.tags.find_one({"_id": object_id})

    if not tag:
        raise NotFound(f"No tag found with ID {tag_id!r}.")

    if not can_manage_tag(tag, get_managed_group_ids(current_user_id())):
        raise Forbidden("You are not allowed to delete this tag.")

    # Best-effort cleanup: also drops references to the deleted tag from items.
    delete_tags_and_references([object_id])

    return jsonify(status="success"), 200
