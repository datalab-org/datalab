import atexit
from functools import lru_cache

import pymongo
from flask_pymongo import PyMongo
from pydantic import BaseModel
from pymongo.errors import ConnectionFailure

from pydatalab.models import ITEM_MODELS

__all__ = (
    "flask_mongo",
    "check_mongo_connection",
    "create_default_indices",
    "_get_active_mongo_client",
    "insert_pydantic_model_fork_safe",
    "ITEMS_FTS_FIELDS",
)

flask_mongo = PyMongo()
"""This is the primary database interface used by the Flask app."""

"""One-liner that pulls all non-semantic string fields out of all item
models implemented for this server.
"""
ITEMS_FTS_FIELDS: set[str] = set().union(
    *(
        {
            f
            for f, p in model.schema(by_alias=False)["properties"].items()
            if (
                p.get("type") == "string"
                and p.get("format") not in ("date-time", "uuid")
                and f != "type"
            )
        }
        for model in ITEM_MODELS.values()
    )
)


def insert_pydantic_model_fork_safe(model: BaseModel, collection: str) -> str:
    """Inserts a Pydantic model into chosen collection, returning the inserted ID."""
    return (
        get_database()[collection]
        .insert_one(model.dict(by_alias=True, exclude_none=True))
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
    from pydatalab.logger import LOGGER

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

    ret += db.export_tasks.create_index(
        "task_id", unique=True, name="unique task ID", background=background
    )
    ret += db.export_tasks.create_index(
        "creator_id", name="export task creator", background=background
    )
    ret += db.export_tasks.create_index(
        "created_at", name="export task created at", background=background
    )
    ret += db.export_tasks.create_index("status", name="export task status", background=background)

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
