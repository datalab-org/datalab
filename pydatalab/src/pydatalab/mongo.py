import atexit
import hashlib
import re
from functools import lru_cache
from typing import Any

import pymongo
from bson import ObjectId
from flask_pymongo import PyMongo
from pydantic import BaseModel
from pymongo.errors import ConnectionFailure

from pydatalab.logger import LOGGER

__all__ = (
    "flask_mongo",
    "check_mongo_connection",
    "create_default_indices",
    "_get_active_mongo_client",
    "insert_pydantic_model_fork_safe",
    "gravatar_hash_for",
    "run_startup_migrations",
    "ITEMS_FTS_FIELDS",
    "USERS_FTS_FIELDS",
    "COLLECTIONS_FTS_FIELDS",
    "GROUPS_FTS_FIELDS",
    "TAGS_FTS_FIELDS",
    "generate_heuristic_regex_search",
    "build_search_pipeline",
    "creators_lookup",
    "groups_lookup",
    "files_lookup",
    "resolve_tags_for_docs",
)

flask_mongo = PyMongo()
"""This is the primary database interface used by the Flask app."""

"""One-liner that pulls all non-semantic string fields out of all item
models implemented for this server.
"""


def creators_lookup() -> dict:
    return {
        "from": "users",
        "let": {"creator_ids": "$creator_ids"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$creator_ids", []]}]}}},
            {"$addFields": {"__order": {"$indexOfArray": ["$$creator_ids", "$_id"]}}},
            {"$sort": {"__order": 1}},
            {"$project": {"_id": 1, "display_name": 1, "gravatar_hash": 1}},
        ],
        "as": "creators",
    }


def groups_lookup() -> dict:
    return {
        "from": "groups",
        "let": {"group_ids": "$group_ids"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$group_ids", []]}]}}},
            {"$addFields": {"__order": {"$indexOfArray": ["$$group_ids", "$_id"]}}},
            {"$sort": {"__order": 1}},
            {"$project": {"_id": 1, "display_name": 1, "group_id": 1}},
        ],
        "as": "groups",
    }


def files_lookup() -> dict:
    return {
        "from": "files",
        "localField": "file_ObjectIds",
        "foreignField": "_id",
        "as": "files",
    }


def resolve_tags_for_docs(docs: list[dict]) -> None:
    """Inline tag details into each doc's `tags` field, in place.

    Tag references (mappings carrying an `immutable_id`) are resolved against
    the `tags` collection with no permission filter: display access is gated
    by the parent entry itself, so every tag on a viewable entry resolves.
    References to deleted tags are dropped.
    """
    tag_ids: set[ObjectId] = set()
    for doc in docs:
        for tag in doc.get("tags") or []:
            if isinstance(tag, dict):
                tag_ids.add(ObjectId(tag["immutable_id"]))

    if not tag_ids:
        return

    resolved = {
        tag_doc["_id"]: tag_doc
        for tag_doc in flask_mongo.db.tags.find(
            {"_id": {"$in": list(tag_ids)}},
            projection={"_id": 1, "name": 1, "description": 1, "color": 1},
        )
    }

    for doc in docs:
        tags = doc.get("tags")
        if not tags:
            continue
        resolved_tags: list = []
        for tag in tags:
            if isinstance(tag, dict):
                match = resolved.get(ObjectId(tag["immutable_id"]))
                # Referenced tag no longer exists: drop it silently.
                if match is None:
                    continue
                resolved_tags.append(
                    {
                        "type": "tags",
                        "immutable_id": str(match["_id"]),
                        "name": match.get("name"),
                        "description": match.get("description"),
                        "color": match.get("color"),
                    }
                )
        doc["tags"] = resolved_tags


@lru_cache(maxsize=1)
def get_items_fts_fields() -> set[str]:
    """Get all string fields from item models for full-text search."""
    from pydatalab.models import ITEM_MODELS

    fields = set()

    for model_name, model in ITEM_MODELS.items():
        schema = model.model_json_schema(by_alias=False)

        model_fields = set()
        for f, p in schema.get("properties", {}).items():
            if f == "type":
                continue

            if p.get("type") == "string" and p.get("format") not in ("date-time", "uuid"):
                model_fields.add(f)
            elif "anyOf" in p:
                for option in p["anyOf"]:
                    if option.get("type") == "string" and option.get("format") not in (
                        "date-time",
                        "uuid",
                    ):
                        model_fields.add(f)
                        break

        fields.update(model_fields)

    return fields


ITEMS_FTS_FIELDS: set[str] = set()

USERS_FTS_FIELDS: set[str] = {"identities.name", "display_name", "contact_email"}
"""Fields to search for users."""

COLLECTIONS_FTS_FIELDS: set[str] = {"collection_id", "title", "description"}
"""Fields to search for collections."""

GROUPS_FTS_FIELDS: set[str] = {"group_id", "display_name", "description"}
"""Fields to search for groups."""

TAGS_FTS_FIELDS: set[str] = {"name", "description"}
"""Fields to search for tags."""


def generate_heuristic_regex_search(
    query: str, fields: set[str], part_length: int = 4
) -> dict[str, Any]:
    """Generate a heuristic regex search object for MongoDB that uses
    word boundaries for short parts of the query, but allows matches anywhere.

    Parameters:
        query: The full search query string.
        fields: Set of field names to search across.
        part_length: The length below which to add a word boundary to the start of the part.

    Returns:
        A MongoDB query object that can be used in a $match stage.

    """

    query_parts = [re.escape(part) for part in query.split(" ") if part.strip()]

    query_parts = [f"\\b{part}" if len(part) <= part_length else part for part in query_parts]
    match_obj = {
        "$or": [
            {"$and": [{field: {"$regex": query, "$options": "i"}} for query in query_parts]}
            for field in fields
        ]
    }
    LOGGER.debug("Performing regex search for %s with full search %s", query_parts, match_obj)

    return match_obj


def build_search_pipeline(
    query: str,
    fields: set[str],
    permissions: dict | None,
) -> list[dict]:
    """Build a MongoDB aggregation pipeline for search with support for FTS, regex, and heuristic modes.

    Parameters:
        query: The search query string.
        fields: Set of field names to search across.
        permissions: Optional permissions filter to apply.

    Returns:
        A list of pipeline stages for MongoDB aggregation.

    """
    pipeline = []
    match_obj: dict[str, Any]

    if isinstance(query, str):
        query = query.strip("'")

    if isinstance(query, str) and query.startswith("%"):
        # Old FTS query style, using MongoDB text indexes
        query = query.lstrip("%")
        query = query.strip("'")
        match_obj = {"$text": {"$search": query}}
        if permissions:
            match_obj.update(permissions)

        pipeline.append({"$match": match_obj})
        pipeline.append({"$sort": {"score": {"$meta": "textScore"}}})

    elif isinstance(query, str) and query.startswith("#"):
        # Plain regex search, without word boundaries or splitting into parts
        query = query.lstrip("#")
        query = query.strip("'")

        match_obj = {"$or": [{field: {"$regex": query, "$options": "i"}} for field in fields]}
        if permissions:
            match_obj = {"$and": [permissions, match_obj]}

        pipeline.append({"$match": match_obj})

    else:
        # Heuristic + regex search, splitting the query into parts and adding word boundaries
        match_obj = generate_heuristic_regex_search(query, fields)
        if permissions:
            match_obj = {"$and": [permissions, match_obj]}

        pipeline.append({"$match": match_obj})

    return pipeline


def insert_pydantic_model_fork_safe(model: BaseModel, collection: str) -> str:
    """Inserts a Pydantic model into chosen collection, returning the inserted ID."""
    return (
        get_database()[collection]
        .insert_one(model.model_dump(by_alias=False, exclude_none=True))
        .inserted_id
    )


@lru_cache(maxsize=1)
def _get_active_mongo_client(timeoutMS: int = 1000) -> pymongo.MongoClient:
    """Returns a `MongoClient` for the configured `MONGO_URI`,
    raising a `RuntimeError` if not available.

    Parameters:
        timeoutMS: Value to use for the MongoDB timeouts (connect and server select)
            in milliseconds

    Returns:
        The active MongoClient, already connected.

    """
    from pydatalab.config import CONFIG

    try:
        client = pymongo.MongoClient(
            CONFIG.MONGO_URI,
            connectTimeoutMS=timeoutMS,
            serverSelectionTimeoutMS=timeoutMS,
            connect=True,
        )

        atexit.register(
            lambda client: client.close(),
            client,
        )
        return client

    except ConnectionFailure as exc:
        LOGGER.critical("Unable to connect to MongoDB at %r: %s", CONFIG.MONGO_URI, exc)
        raise RuntimeError from exc


@lru_cache(maxsize=1)
def get_database() -> pymongo.database.Database:
    """Returns the configured database."""
    return _get_active_mongo_client().get_database()


def check_mongo_connection() -> None:
    """Checks that the configured MongoDB is available and returns a
    `pymongo.MongoClient` for the configured `MONGO_URI`.

    Raises:
        RuntimeError:
            If the configured MongoDB is not available.

    """
    try:
        cli = _get_active_mongo_client()
        cli.list_database_names()
    except Exception as exc:
        raise RuntimeError from exc


def create_default_indices(
    client: pymongo.MongoClient | None = None,
    background: bool = False,
) -> list[str]:
    """Creates indices for the configured or passed MongoClient.

    Indexes created are:
        - A text index over all string fields in item models,
        - An index over item type,
        - A unique index over `item_id` and `refcode`.
        - A text index over user names and identities.
        - Version control indexes:
            - Index on item_versions.refcode for fast version history lookup
            - Index on item_versions.user_id for fast user contribution queries
            - Compound index on (refcode, version) for sorted version history
            - Unique index on version_counters.refcode for atomic version numbering

    Parameters:
        background: If true, indexes will be created as background jobs.

    Returns:
        A list of messages returned by each `create_index` call.

    """

    global ITEMS_FTS_FIELDS

    if not ITEMS_FTS_FIELDS:
        ITEMS_FTS_FIELDS = get_items_fts_fields()

    if not ITEMS_FTS_FIELDS:
        raise ValueError("Cannot create text indices: no fields available for full-text search")

    if client is None:
        client = _get_active_mongo_client()
    db = client.get_database()

    def create_or_recreate_text_index(collection, fields, weights):
        fts_index_name = f"{collection.name} full-text search"

        def create_fts():
            return collection.create_index(
                [(k, pymongo.TEXT) for k in fields],
                name=fts_index_name,
                weights=weights,
            )

        try:
            return create_fts()
        except pymongo.errors.OperationFailure:
            collection.drop_index(fts_index_name)
            return create_fts()

    ret = []

    ret += create_or_recreate_text_index(
        db.items,
        ITEMS_FTS_FIELDS,
        weights={"refcode": 3, "item_id": 3, "name": 3, "chemform": 3},
    )

    ret += create_or_recreate_text_index(
        db.collections,
        ["collection_id", "title", "description"],
        weights={"collection_id": 3, "title": 3, "description": 3},
    )

    ret += create_or_recreate_text_index(
        db.tags,
        ["name", "description"],
        weights={"name": 3, "description": 1},
    )

    ret += db.items.create_index("type", name="item type", background=background)
    ret += db.items.create_index(
        "item_id", unique=True, name="unique item ID", background=background
    )
    ret += db.items.create_index(
        "refcode", unique=True, name="unique refcode", background=background
    )
    ret += db.items.create_index("last_modified", name="last modified", background=background)

    ret += db.items.create_index("date", name="date", background=background)

    user_fts_fields = {"identities.name", "display_name"}

    user_index_name = "unique user identifiers"

    def create_user_index(user_index_name):
        return db.users.create_index(
            [
                ("identities.identifier", pymongo.ASCENDING),
                ("identities.identity_type", pymongo.ASCENDING),
            ],
            unique=True,
            partialFilterExpression={"identities": {"$exists": True}},
            name=user_index_name,
            background=background,
        )

    try:
        ret += create_user_index(user_index_name)
    except pymongo.errors.OperationFailure:
        db.users.drop_index(user_index_name)
        ret += create_user_index(user_index_name)

    user_fts_name = "user identities full-text search"

    def create_user_fts():
        return db.users.create_index(
            [(k, pymongo.TEXT) for k in user_fts_fields],
            name=user_fts_name,
            background=background,
        )

    try:
        ret += create_user_fts()
    except pymongo.errors.OperationFailure:
        db.users.drop_index(user_fts_name)
        ret += create_user_fts()

    group_fts_fields = {"display_name", "description"}
    group_fts_name = "group full-text search"
    group_index_name = "unique group identifiers"

    def create_group_index(group_index_name):
        return db.groups.create_index(
            "group_id",
            unique=True,
            name=group_index_name,
            background=background,
        )

    try:
        ret += create_group_index(group_index_name)
    except pymongo.errors.OperationFailure:
        db.users.drop_index(group_index_name)
        ret += create_group_index(group_index_name)

    def create_group_fts():
        return db.groups.create_index(
            [(k, pymongo.TEXT) for k in group_fts_fields],
            name=group_fts_name,
            background=background,
        )

    try:
        ret += create_group_fts()
    except pymongo.errors.OperationFailure:
        db.users.drop_index(group_fts_name)
        ret += create_group_fts()

    ret += db.tasks.create_index(
        "task_id", unique=True, name="unique task ID", background=background
    )

    ret += db.tasks.create_index("type", name="task type", background=background)
    ret += db.tasks.create_index("creator_id", name="task creator", background=background)
    ret += db.tasks.create_index("created_at", name="task created at", background=background)
    ret += db.tasks.create_index("status", name="task status", background=background)
    ret += db.tasks.create_index(
        [("type", pymongo.ASCENDING), ("creator_id", pymongo.ASCENDING)],
        name="task type and creator",
        background=background,
    )

    # Version control indexes
    ret += db.item_versions.create_index("refcode", name="version refcode", background=background)
    ret += db.item_versions.create_index("user_id", name="version user_id", background=background)
    ret += db.item_versions.create_index(
        [("refcode", pymongo.ASCENDING), ("version", pymongo.DESCENDING)],
        name="refcode and version",
        background=background,
    )
    ret += db.version_counters.create_index(
        "refcode", unique=True, name="unique refcode counter", background=background
    )

    return ret


def gravatar_hash_for(email: str | None, display_name: str | None = None) -> str | None:
    """Return the MD5 hash used by the frontend to look up a Gravatar avatar.

    Prefers the trimmed, lowercased contact email (which Gravatar indexes); falls
    back to hashing the display name so a deterministic identicon can still be
    rendered when no email is available. Returns ``None`` if neither is set.
    """
    payload = (str(email) if email else "").strip().lower() or (
        str(display_name) if display_name else ""
    ).strip()
    if not payload:
        return None
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def _backfill_user_gravatar_hashes(db) -> int:
    """Populate `gravatar_hash` on any user doc that lacks it."""
    updates: list[pymongo.UpdateOne] = []
    for user in db.users.find(
        {"gravatar_hash": {"$exists": False}},
        {"_id": 1, "contact_email": 1, "display_name": 1},
    ):
        updates.append(
            pymongo.UpdateOne(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "gravatar_hash": gravatar_hash_for(
                            user.get("contact_email"), user.get("display_name")
                        )
                    }
                },
            )
        )
    if updates:
        db.users.bulk_write(updates, ordered=False)
    return len(updates)


STARTUP_MIGRATIONS = (_backfill_user_gravatar_hashes,)
"""Idempotent one-shot DB fixups run at app startup, after index creation.

Each entry takes a pymongo database handle and returns the number of documents
updated. Keep migrations idempotent and cheap — they run on every boot.
"""


def run_startup_migrations(client: pymongo.MongoClient | None = None) -> dict[str, int]:
    """Run each migration in :data:`STARTUP_MIGRATIONS` against the configured DB."""
    if client is None:
        client = _get_active_mongo_client()
    db = client.get_database()
    results: dict[str, int] = {}
    for migration in STARTUP_MIGRATIONS:
        count = migration(db)
        results[migration.__name__] = count
        if count:
            LOGGER.info("Startup migration %s updated %d document(s)", migration.__name__, count)
    return results
