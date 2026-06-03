"""Version control utilities for item versioning, for use in item routes."""

import datetime

from flask import request
from flask_login import current_user
from pydantic import ValidationError
from werkzeug.exceptions import NotFound

from pydatalab.logger import LOGGER
from pydatalab.models import ItemVersion
from pydatalab.models.versions import VersionAction, VersionCounter
from pydatalab.mongo import flask_mongo

KNOWN_USER_AGENTS = ["Datalab Python API", "datalab-beholder", "datalab-cheminventory-plugin"]
"""User agents that are treated as special values for versioning purposes,
e.g., to identify automated saves vs. user-initiated saves.

No other agent should be stored to avoid incidental fingerprinting.

"""


def apply_protected_fields(restored_data: dict, current_item: dict) -> dict:
    """Apply protected field values from current item to restored data.

    Protected fields cannot be overwritten during restore to maintain data integrity, e.g.,

    - refcode: Immutable identifier
    - _id: Database primary key
    - immutable_id: Database ObjectId reference
    - creator_ids: Ownership/permissions information
    - file_ObjectIds: File attachments managed separately
    - version: Always increments forward to prevent collisions

    Args:
        restored_data: The data being restored from a previous version
        current_item: The current item in the database

    Returns:
        Modified restored_data with protected fields preserved from current_item
    """
    protected_fields = [
        "refcode",
        "_id",
        "immutable_id",
        "creator_ids",
        "file_ObjectIds",
        "version",
    ]

    for field in protected_fields:
        if field in current_item:
            restored_data[field] = current_item[field]

    return restored_data


def get_next_version_number(refcode: str) -> int:
    """Atomically get and increment the version counter for an item.

    Uses a separate counters collection to track version numbers atomically.
    This prevents race conditions when multiple users save versions simultaneously.

    Args:
        refcode: The refcode to get the next version number for

    Returns:
        The next version number (1-indexed)

    """
    result = flask_mongo.db.version_counters.find_one_and_update(
        {"refcode": refcode},
        {"$inc": {"counter": 1}},
        upsert=True,
        return_document=True,  # Return the document after update
    )

    # Validate the result with Pydantic
    try:
        counter_doc = VersionCounter(**result)
        return counter_doc.counter
    except ValidationError as exc:
        LOGGER.error(
            "Version counter validation failed for refcode %s: %s",
            refcode,
            str(exc),
        )
        # Fallback: return raw counter value to prevent blocking saves
        # This should only happen if the document is corrupted
        return result["counter"]


def save_version_snapshot(
    refcode: str,
    action: VersionAction | None = None,
    permission_filter: dict | None = None,
) -> tuple[dict, int]:
    """Save the current state of an item as a version snapshot.

    IMPORTANT: Must be called from a Flask route handler (requires flask-login context).

    Helper function for creating version snapshots with proper audit trail.

    Args:
        refcode: The refcode of the item to save a version for
        action: The reason for saving this version (VersionAction enum): if None,
                it will be set to VersionAction.AGENT_SAVE if the user agent matches a known agent,
                or VersionAction.MANUAL_SAVE otherwise.
        permission_filter: Optional MongoDB filter to apply for permission checking.
            If None, no permission check is performed.

    Returns:
        Tuple of (response_dict, status_code)
    """
    from pydatalab import __version__
    from pydatalab.config import CONFIG

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    # Build query with optional permission filter
    query = {"refcode": refcode}
    if permission_filter:
        query.update(permission_filter)

    item = flask_mongo.db.items.find_one(query)
    if not item:
        raise NotFound(f"Item {refcode} not found.")

    # Skip creating a new version if content is identical to the last snapshot.
    # Excludes fields that change mechanically on every save and don't reflect real edits.
    _MECHANICAL_FIELDS = {"last_modified", "version", "_id"}
    last_version = flask_mongo.db.item_versions.find_one(
        {"refcode": refcode}, sort=[("version", -1)]
    )
    if last_version:
        current_data = {k: v for k, v in item.items() if k not in _MECHANICAL_FIELDS}
        last_data = {k: v for k, v in last_version["data"].items() if k not in _MECHANICAL_FIELDS}
        if current_data == last_data:
            return {"status": "success", "message": "No changes detected, version not saved."}, 200

    # Atomically get the next version number
    next_version_number = get_next_version_number(refcode)

    # Extract user information for hybrid storage approach
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.person.immutable_id

    software_version = __version__

    # Only store user agent if it matches a known agent
    _user_agent = request.headers.get("User-Agent", "unknown")
    user_agent = None
    for known_agent in KNOWN_USER_AGENTS:
        if _user_agent.startswith(known_agent):
            user_agent = _user_agent
            break
    if user_agent is not None and action is None:
        action = VersionAction.AGENT_SAVE

    action = VersionAction.MANUAL_SAVE if action is None else action

    version_entry = {
        "refcode": refcode,
        "version": next_version_number,
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
        "action": action,  # Audit trail: why this version was created
        "user_id": user_id,  # ObjectId for efficient querying
        "datalab_version": software_version,
        "data": item,  # Complete snapshot of the item at this version
        "user_agent": user_agent,  # "What" changed the item
    }

    # Validate with Pydantic before inserting
    try:
        validated_version = ItemVersion(**version_entry)
    except ValidationError as exc:
        LOGGER.error(
            "Version snapshot validation failed for item %s: %s",
            refcode,
            str(exc),
        )
        return (
            {
                "status": "error",
                "message": f"Version data validation failed: {str(exc)}",
                "output": str(exc),
            },
            400,
        )

    # Insert validated data (convert to dict and exclude None values)
    flask_mongo.db.item_versions.insert_one(
        validated_version.dict(by_alias=True, exclude_none=True)
    )
    return (
        {"status": "success", "message": "Version saved.", "version": next_version_number},
        200,
    )


def check_version_access(refcode: str, user_only: bool = False) -> tuple[bool, dict | None]:
    """Check if the current user has access to versions of an item.

    IMPORTANT: Must be called from a Flask route handler (requires permission context).

    Args:
        refcode: The refcode of the item
        user_only: If True, check for write access (user must be a creator).
                  If False, check for read access (public items included).

    Returns:
        Returns (True, item_dict) if user has access, (False, None) otherwise

    """
    from pydatalab.config import CONFIG
    from pydatalab.permissions import get_default_permissions

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    query = {"refcode": refcode}
    query.update(get_default_permissions(user_only=user_only))

    item = flask_mongo.db.items.find_one(query, {"refcode": 1, "_id": 1})
    if not item:
        return False, None

    return True, item
