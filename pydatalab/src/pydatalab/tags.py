"""Tag utilities, for use in item and tag routes."""

from collections.abc import Iterable

from bson import ObjectId
from werkzeug.exceptions import Forbidden

from pydatalab.models.tags import TagAccessScope
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import (
    current_user_group_ids,
    current_user_id,
    is_admin,
    is_admin_sudo_request,
)

__all__ = (
    "get_usable_tags_filter",
    "get_listable_tags_filter",
    "can_manage_tag",
    "delete_tags_and_references",
    "strip_tag_display_fields",
    "tag_immutable_ids",
    "authorize_added_tags",
)


def get_usable_tags_filter(
    user_id: ObjectId | None, group_ids: Iterable[ObjectId] | None = None
) -> dict:
    """The Mongo filter for tags the given user may use (i.e., add to items).

    This is global tags, the user's own user-defined tags and the group tags of the
    groups in `group_ids` (the groups the user is a member of).
    """
    if user_id is None:
        return {"scope": TagAccessScope.GLOBAL.value}

    conditions: list[dict] = [{"scope": TagAccessScope.GLOBAL.value}, {"owner": user_id}]
    group_ids = list(group_ids or [])
    if group_ids:
        conditions.append({"scope": TagAccessScope.GROUP.value, "owner": {"$in": group_ids}})
    return {"$or": conditions}


def get_listable_tags_filter(managed_group_ids: Iterable[ObjectId]) -> dict:
    """The Mongo filter for the tags the current user may list on the tag management page.

    This is the tags they may use (see `get_usable_tags_filter`) plus the tags of the
    groups they manage without being a member. Like for items, administrators are
    treated as normal users unless in super-user mode (`?sudo=1`), where they list all
    tags, including other users' user-defined tags and all group tags.

    Parameters:
        managed_group_ids: The IDs of the groups managed by the current user (see
            `pydatalab.permissions.get_managed_group_ids`).

    """
    if is_admin_sudo_request():
        return {}

    user_id = current_user_id()
    usable = get_usable_tags_filter(user_id, current_user_group_ids())

    managed_group_ids = list(managed_group_ids)
    if user_id is None or not managed_group_ids:
        return usable

    manageable = {"scope": TagAccessScope.GROUP.value, "owner": {"$in": managed_group_ids}}
    return {"$or": [usable, manageable]}


def can_manage_tag(tag_doc: dict, managed_group_ids: Iterable[ObjectId]) -> bool:
    """Whether the current user may edit or delete the given tag document.

    Administrators may manage every tag. Otherwise:

    - global tags cannot be managed;
    - user-defined tags require the owner;
    - group tags require one of the group's managers.

    Parameters:
        tag_doc: The tag document, with `scope` and `owner` as stored in the database.
        managed_group_ids: The IDs of the groups managed by the current user (see
            `pydatalab.permissions.get_managed_group_ids`), passed in so that many tags
            can be checked with a single lookup.

    """
    if is_admin():
        return True

    scope = tag_doc.get("scope")

    if scope == TagAccessScope.USER.value:
        user_id = current_user_id()
        return user_id is not None and tag_doc.get("owner") == user_id

    if scope == TagAccessScope.GROUP.value:
        return tag_doc.get("owner") in set(managed_group_ids)

    return False


def delete_tags_and_references(tag_ids: list[ObjectId]) -> None:
    """Delete the given tags and drop their references from items.

    Like collection deletion, the cleanup of items is a raw update that does NOT go
    through the item save route, so it neither bumps `last_modified` nor creates a new
    item version.

    This hardcodes `items` as the only `HasTags` collection. Extend it if `HasTags` is
    applied to other entities. Note that references are not deleted from
    item_versions, so a reference to a deleted tag can survive there.
    """
    if not tag_ids:
        return

    flask_mongo.db.tags.delete_many({"_id": {"$in": tag_ids}})
    flask_mongo.db.items.update_many(
        {"tags": {"$elemMatch": {"immutable_id": {"$in": tag_ids}, "type": "tags"}}},
        {"$pull": {"tags": {"immutable_id": {"$in": tag_ids}, "type": "tags"}}},
    )


def strip_tag_display_fields(item: dict) -> None:
    """Reduce tag references in ``item['tags']`` to the minimal
    ``{type, immutable_id}`` link before storage, in place.

    The display fields (name/description/color) are inlined by the client and
    re-resolved on every read (`resolve_tags_for_docs`), so persisting them would
    be redundant denormalisation.
    """
    tags = item.get("tags")
    if not isinstance(tags, list):
        return
    item["tags"] = [
        {"type": "tags", "immutable_id": tag["immutable_id"]}
        for tag in tags
        if isinstance(tag, dict) and tag.get("immutable_id") is not None
    ]


def tag_immutable_ids(tags) -> set[str]:
    """Collect the string `immutable_id`s of the tag references in a `tags` list."""
    if not isinstance(tags, list):
        return set()
    return {
        str(tag["immutable_id"])
        for tag in tags
        if isinstance(tag, dict) and tag.get("immutable_id") is not None
    }


def authorize_added_tags(tags, existing_tag_ids: set[str]) -> None:
    """Reject any newly added tag that the current user may not use.

    A user may add global tags, their own user-defined tags and the group tags of the
    groups they belong to; any other reference (including to a tag that does not
    exist) is rejected.
    """
    added_ids = tag_immutable_ids(tags) - existing_tag_ids
    if not added_ids:
        return

    usable_count = flask_mongo.db.tags.count_documents(
        {
            "_id": {"$in": [ObjectId(i) for i in added_ids]},
            **get_usable_tags_filter(current_user_id(), current_user_group_ids()),
        }
    )
    if usable_count != len(added_ids):
        raise Forbidden(
            "You cannot add a tag that does not exist, is owned by another user, "
            "or belongs to a group you are not a member of."
        )
