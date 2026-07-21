"""Central helpers for the `blocks` and `block_versions` collections.

This module is the single chokepoint for reading and writing separated block
documents, and for the branching logic between the two coexisting storage
forms of an item's `blocks_obj` entry:

- **Embedded (legacy)**: the full block payload stored inline in the item
  document. Legacy blocks are frozen in this form — they are read, written,
  versioned, and restored exactly as before blocks were separated, and are
  never converted.
- **Reference (new)**: a ``{"immutable_id": ObjectId}`` pointer to a document
  in the `blocks` collection, which is the source of truth for the payload.
  Only blocks created after the separation are in this form. Item version
  snapshots store version-pinned references ``{"immutable_id", "version"}``
  that point at `block_versions` entries.

Security invariant: the parent item is the sole authority for reading block
content. Every function here that returns block (or block-version) payloads
must only be called downstream of an already-authorized item read — no route
may authorize block content by the block document's own owner fields, and no
direct `blocks`/`block_versions` listing or fetch-by-id endpoint may exist.
"""

import datetime
from typing import TYPE_CHECKING, Any

from bson import ObjectId
from flask_login import current_user
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, NotFound

from pydatalab.logger import LOGGER
from pydatalab.models.blocks import Block
from pydatalab.models.versions import BlockVersion, VersionAction
from pydatalab.mongo import flask_mongo

if TYPE_CHECKING:
    from pydatalab.blocks.base import DataBlock

__all__ = (
    "is_block_reference",
    "authorize_and_get_form",
    "load_blocks_obj",
    "resolve_snapshot_blocks_obj",
    "create_block_document",
    "update_block_document",
    "delete_block_document",
    "snapshot_block_version",
    "restore_block_version",
)

_REFERENCE_KEYS = {"immutable_id", "version"}


def _now_isoformat() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def _current_user_id() -> ObjectId | None:
    if current_user and current_user.is_authenticated:
        return current_user.person.immutable_id
    return None


def is_block_reference(entry: Any) -> bool:
    """Whether a stored `blocks_obj` entry is a reference to a `blocks` document
    (``{"immutable_id": ...}``) rather than a legacy embedded block.
    """
    return (
        isinstance(entry, dict) and "immutable_id" in entry and set(entry.keys()) <= _REFERENCE_KEYS
    )


def authorize_and_get_form(item_id: str | None, block_id: str) -> dict | None:
    """The single permissioned query at the head of every block write.

    Checks in one query that the current user has write access to the item and
    returns the stored `blocks_obj` entry for `block_id` (embedded payload or
    reference).

    Returns:
        The stored `blocks_obj` entry, or `None` if the item has no entry for
        this `block_id`.
    """
    from pydatalab.permissions import get_default_permissions

    if not item_id:
        raise BadRequest("`item_id` must be provided when saving a block.")

    item = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {f"blocks_obj.{block_id}": 1},
    )
    if not item:
        raise NotFound(f"Could not find item {item_id!r} with write access to save block to.")

    return (item.get("blocks_obj") or {}).get(block_id)


def load_blocks_obj(parent_doc: dict) -> dict[str, Any]:
    """Resolve a live parent document's `blocks_obj` into full payloads keyed by
    `block_id`, i.e., the API shape used before blocks were separated.

    Embedded entries pass through verbatim; referenced entries are resolved from
    the `blocks` collection in a single batched query. Must only be called on a
    document the caller is already authorized to read.
    """
    blocks_obj = parent_doc.get("blocks_obj") or {}
    referenced: dict[str, ObjectId] = {
        block_id: entry["immutable_id"]
        for block_id, entry in blocks_obj.items()
        if is_block_reference(entry)
    }

    resolved_docs: dict[ObjectId, dict] = {}
    if referenced:
        resolved_docs = {
            doc["_id"]: doc
            for doc in flask_mongo.db.blocks.find(
                {"_id": {"$in": list(referenced.values())}}, {"data": 1}
            )
        }

    loaded: dict[str, Any] = {}
    for block_id, entry in blocks_obj.items():
        if block_id not in referenced:
            loaded[block_id] = entry
            continue
        doc = resolved_docs.get(referenced[block_id])
        if doc is None:
            LOGGER.error(
                "Dangling block reference: blocks_obj[%r] points at missing blocks doc %s",
                block_id,
                referenced[block_id],
            )
            continue
        loaded[block_id] = doc.get("data", {})

    return loaded


def resolve_snapshot_blocks_obj(snapshot_data: dict) -> dict[str, Any]:
    """Resolve an `item_versions` snapshot's `blocks_obj` into full payloads keyed
    by `block_id`.

    Embedded entries pass through verbatim; version-pinned references
    ``{"immutable_id", "version"}`` are resolved from `block_versions` in a single
    batched query.
    Must only be called downstream of an authorized item(-version) read.
    """
    blocks_obj = snapshot_data.get("blocks_obj") or {}

    referenced: dict[str, tuple[ObjectId, int]] = {
        block_id: (entry["immutable_id"], entry["version"])
        for block_id, entry in blocks_obj.items()
        if is_block_reference(entry) and entry.get("version") is not None
    }

    resolved_versions: dict[tuple[ObjectId, int], dict] = {}
    if referenced:
        resolved_versions = {
            (doc["block_immutable_id"], doc["version"]): doc
            for doc in flask_mongo.db.block_versions.find(
                {
                    "$or": [
                        {"block_immutable_id": immutable_id, "version": version}
                        for immutable_id, version in referenced.values()
                    ]
                },
                {"block_immutable_id": 1, "version": 1, "data": 1},
            )
        }

    resolved: dict[str, Any] = {}
    for block_id, entry in blocks_obj.items():
        if not is_block_reference(entry):
            resolved[block_id] = entry
            continue
        doc = resolved_versions.get(referenced[block_id]) if block_id in referenced else None
        if doc is None:
            LOGGER.error(
                "Dangling block reference in version snapshot: blocks_obj[%r] -> %s",
                block_id,
                entry,
            )
            continue
        resolved[block_id] = doc.get("data", {})

    return resolved


def create_block_document(block: "DataBlock") -> ObjectId:
    """Insert a new `blocks` document for a newly created block and return its
    immutable ID, to be used as reference.

    The new document starts with no committed version (`version` 0); its first
    `block_versions` entry is cut by the next item version snapshot. Ownership
    fields are populated with the creating user only. Access to the block
    depends on the item.
    """
    creator_id = _current_user_id()
    block_doc = Block(
        block_id=block.block_id,
        blocktype=block.blocktype,
        data=block.to_db(),
        creator_ids=[creator_id] if creator_id else [],
        last_modified=_now_isoformat(),
    )

    result = flask_mongo.db.blocks.insert_one(
        block_doc.model_dump(exclude={"immutable_id", "creators", "groups"})
    )
    if not result.acknowledged:
        raise RuntimeError(f"Failed to insert new block document for block {block.block_id!r}.")

    return result.inserted_id


def update_block_document(immutable_id: ObjectId, data: dict) -> None:
    """Overwrite the live payload of a referenced block (`data` sub-document).

    Writes the live document only: no `block_versions` entry is created and the
    `version` counter is not bumped.
    """
    result = flask_mongo.db.blocks.update_one(
        {"_id": immutable_id},
        {"$set": {"data": data, "last_modified": _now_isoformat()}},
    )
    if result.matched_count != 1:
        raise BadRequest(f"Failed to save block: no block document found for {immutable_id}.")


def delete_block_document(immutable_id: ObjectId) -> None:
    """Remove a referenced block's live document.

    Its `block_versions` history is retained so that item versions
    pinning it remain restorable. Mirrors `item_versions`.
    """
    flask_mongo.db.blocks.delete_one({"_id": immutable_id})


def snapshot_block_version(
    immutable_id: ObjectId,
    action: VersionAction = VersionAction.MANUAL_SAVE,
    user_id: ObjectId | None = None,
) -> int | None:
    """Cut a `block_versions` entry for a referenced block if its live payload
    has changed since its last committed version, and return the block's
    now-current committed version number.

    If no live `blocks` document exists (e.g. the block was deleted between the
    caller's item read and now — deletion retains history), falls back to
    re-pinning the latest committed version. Returns `None` only when there is
    no live document *and* no committed history, i.e. there is no content
    anywhere to snapshot.
    """
    from pydatalab import __version__

    block_doc = flask_mongo.db.blocks.find_one({"_id": immutable_id})
    if not block_doc:
        last_version = flask_mongo.db.block_versions.find_one(
            {"block_immutable_id": immutable_id},
            {"version": 1, "_id": 0},
            sort=[("version", -1)],
        )
        return last_version["version"] if last_version else None

    data = block_doc.get("data", {})

    last_version = flask_mongo.db.block_versions.find_one(
        {"block_immutable_id": immutable_id}, sort=[("version", -1)]
    )
    if last_version and last_version.get("data") == data:
        return last_version["version"]

    updated_doc = flask_mongo.db.blocks.find_one_and_update(
        {"_id": immutable_id},
        {"$inc": {"version": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if updated_doc is None:
        return None
    next_version = updated_doc["version"]

    version_entry = BlockVersion(
        block_immutable_id=immutable_id,
        block_id=block_doc["block_id"],
        version=next_version,
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        action=action,
        user_id=user_id if user_id is not None else _current_user_id(),
        datalab_version=__version__,
        data=data,
    )

    # Restore the raw payload into 'data' so that None-valued fields are not
    # stripped by model_dump(exclude_none=True), mirroring item snapshots.
    version_doc = version_entry.model_dump(exclude_none=True)
    version_doc["data"] = data
    try:
        flask_mongo.db.block_versions.insert_one(version_doc)
    except DuplicateKeyError:
        # A concurrent snapshot minted this version number first; both captured
        # the same live payload, so re-pinning the number is safe.
        LOGGER.warning(
            "Concurrent block version snapshot for block %s (version %d)",
            immutable_id,
            next_version,
        )

    return next_version


def restore_block_version(
    immutable_id: ObjectId,
    version: int,
    user_id: ObjectId | None = None,
) -> int | None:
    """Append-only restore of a version-pinned block reference.

    Writes the pinned `block_versions` payload back as the new current state of
    the live `blocks` document and creates a new RESTORED `block_versions` entry.
    Returns the new committed version number, or `None` (restoring nothing) if no
    matching `block_versions` entry exists.
    """
    from pydatalab import __version__

    pinned = flask_mongo.db.block_versions.find_one(
        {"block_immutable_id": immutable_id, "version": version}
    )
    if not pinned:
        LOGGER.error(
            "Cannot restore block %s to version %s: no such block_versions entry",
            immutable_id,
            version,
        )
        return None

    latest = flask_mongo.db.block_versions.find_one(
        {"block_immutable_id": immutable_id},
        {"version": 1, "_id": 0},
        sort=[("version", -1)],
    )
    next_version = (latest["version"] if latest else 0) + 1

    data = pinned["data"]
    if user_id is None:
        user_id = _current_user_id()

    # Build the full Block model so that a recreated document contains all
    # the fields.
    block_doc = Block(
        block_id=pinned["block_id"],
        blocktype=data.get("blocktype", "unknown"),
        data=data,
        version=next_version,
        last_modified=_now_isoformat(),
        creator_ids=[user_id] if user_id else [],
    )
    envelope = block_doc.model_dump(exclude={"immutable_id", "creators", "groups"})
    set_fields = {
        field: envelope.pop(field)
        for field in ("data", "version", "last_modified", "block_id", "blocktype", "type")
    }

    flask_mongo.db.blocks.update_one(
        {"_id": immutable_id},
        {"$set": set_fields, "$setOnInsert": envelope},
        upsert=True,
    )

    version_entry = BlockVersion(
        block_immutable_id=immutable_id,
        block_id=pinned["block_id"],
        version=next_version,
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        action=VersionAction.RESTORED,
        restored_from_version=pinned["_id"],
        user_id=user_id,
        datalab_version=__version__,
        data=data,
    )
    version_doc = version_entry.model_dump(exclude_none=True)
    version_doc["data"] = data
    flask_mongo.db.block_versions.insert_one(version_doc)

    return next_version
