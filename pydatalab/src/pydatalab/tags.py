"""Tag utilities, for use in item and tag routes."""

from bson import ObjectId
from flask_login import current_user
from werkzeug.exceptions import Forbidden

from pydatalab.config import CONFIG
from pydatalab.models.tags import TagAccessScope
from pydatalab.mongo import flask_mongo

__all__ = (
    "get_usable_tags_filter",
    "strip_tag_display_fields",
    "tag_immutable_ids",
    "authorize_added_tags",
)


def get_usable_tags_filter(user_id: ObjectId | None) -> dict:
    """The Mongo filter for tags the given user may list and use.

    This is global tags plus the user's own user-defined tags.
    """
    if user_id is None:
        return {"scope": TagAccessScope.GLOBAL.value}
    return {"$or": [{"scope": TagAccessScope.GLOBAL.value}, {"owner": user_id}]}


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

    A user may add global tags and their own user-defined tags; any other
    reference (including to a tag that does not exist) is rejected.
    """
    # In testing an unauthenticated "public" user can write.
    if CONFIG.TESTING and not current_user.is_authenticated:
        return

    added_ids = tag_immutable_ids(tags) - existing_tag_ids
    if not added_ids:
        return

    usable_count = flask_mongo.db.tags.count_documents(
        {
            "_id": {"$in": [ObjectId(i) for i in added_ids]},
            **get_usable_tags_filter(current_user.person.immutable_id),
        }
    )
    if usable_count != len(added_ids):
        raise Forbidden("You cannot add a tag that does not exist or is owned by another user.")
