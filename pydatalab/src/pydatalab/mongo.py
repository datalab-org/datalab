import atexit
from functools import lru_cache

# Must be imported in this way to allow for easy patching with mongomock
import pymongo
from flask_pymongo import PyMongo
from pydantic import BaseModel
from pymongo.errors import ConnectionFailure

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


def _get_items_fts_fields() -> set[str]:
    """Get all string fields from item models for full-text search."""
    fields = set()
    try:
        from pydatalab.logger import LOGGER
        from pydatalab.models import ITEM_MODELS

        LOGGER.info(f"Available models: {list(ITEM_MODELS.keys())}")

        for model_name, model in ITEM_MODELS.items():
            LOGGER.info(f"Processing model: {model_name}")
            try:
                schema = model.model_json_schema(by_alias=False)
                LOGGER.info(f"Schema for {model_name}: {schema.get('properties', {}).keys()}")

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

                LOGGER.info(f"String fields found for {model_name}: {model_fields}")
                fields.update(model_fields)
            except Exception as model_error:
                LOGGER.error(f"Error processing model {model_name}: {model_error}")

    except Exception as e:
        from pydatalab.logger import LOGGER

        LOGGER.warning(f"Failed to extract FTS fields from models: {e}")
        fields = {"item_id", "name", "description", "refcode", "synthesis_description", "supplier"}

    from pydatalab.logger import LOGGER

    LOGGER.info(f"Final FTS fields: {fields}")
    return fields


ITEMS_FTS_FIELDS: set[str] = set()


def insert_pydantic_model_fork_safe(model: BaseModel, collection: str) -> str:
    """Inserts a Pydantic model into chosen collection, returning the inserted ID."""
    return (
        get_database()[collection]
        .insert_one(model.model_dump(by_alias=True, exclude_none=True))
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
        LOGGER.critical(f"Unable to connect to MongoDB at {CONFIG.MONGO_URI!r}: {exc}")
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

    Parameters:
        background: If true, indexes will be created as background jobs.

    Returns:
        A list of messages returned by each `create_index` call.

    """

    from pydatalab.logger import LOGGER

    global ITEMS_FTS_FIELDS

    if not ITEMS_FTS_FIELDS:
        LOGGER.info("ITEMS_FTS_FIELDS is empty, calculating...")
        ITEMS_FTS_FIELDS = _get_items_fts_fields()
        LOGGER.info(f"Calculated ITEMS_FTS_FIELDS: {ITEMS_FTS_FIELDS}")

    if not ITEMS_FTS_FIELDS:
        LOGGER.error("ITEMS_FTS_FIELDS is still empty after calculation")
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

    return ret
