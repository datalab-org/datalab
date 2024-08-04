from typing import List, Optional

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
)

flask_mongo = PyMongo()
"""This is the primary database interface used by the Flask app."""


def insert_pydantic_model_fork_safe(model: BaseModel, collection: str) -> str:
    """Inserts a Pydantic model into chosen collection, returning the inserted ID."""
    return (
        get_database()[collection]
        .insert_one(model.dict(by_alias=True, exclude_none=True))
        .inserted_id
    )


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
        return pymongo.MongoClient(
            CONFIG.MONGO_URI,
            connectTimeoutMS=timeoutMS,
            serverSelectionTimeoutMS=timeoutMS,
            connect=True,
        )
    except ConnectionFailure as exc:
        LOGGER.critical(f"Unable to connect to MongoDB at {CONFIG.MONGO_URI}")
        raise RuntimeError from exc


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
    client: Optional[pymongo.MongoClient] = None,
    background: bool = False,
    allow_rebuild: bool = False,
) -> List[str]:
    """Creates indices for the configured or passed MongoClient.

    Indexes created are:
        - A text index over all string fields in item models,
        - An index over item type,
        - A unique index over `item_id` and `refcode`.
        - A text index over user names and identities.

    Parameters:
        client: The MongoClient to use. If None, a new one will be created.
        background: If true, indexes will be created as background jobs.
        allow_rebuild: If true, named indexes will be recreated if they already exist
            with alternative options.

    Returns:
        A list of messages returned by each `create_index` call.

    """
    from pydatalab.models import ITEM_MODELS

    if client is None:
        client = _get_active_mongo_client()
    db = client.get_database()

    item_fts_fields = set()
    for model in ITEM_MODELS:
        schema = ITEM_MODELS[model].schema()
        for f in schema["properties"]:
            if schema["properties"][f].get("type") == "string":
                item_fts_fields.add(f)

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
        item_fts_fields,
        weights={"refcode": 3, "item_id": 3, "name": 3, "chemform": 3},
    )

    ret += create_or_recreate_text_index(
        db.collections,
        ["collection_id", "title", "description"],
        weights={"collection_id": 3, "title": 3, "description": 3},
    )

    indices = [
        {"type": {"name": "item type", "background": background}},
        {"item_id": {"name": "unique item ID", "unique": True, "background": background}},
        {"refcode": {"name": "unique refcode", "unique": True, "background": background}},
        {"last_modified": {"name": "last modified", "background": background}},
        {"creator_ids": {"name": "creators", "background": background}},
        {"_deleted": {"name": "deleted items", "background": background}},
    ]

    for index in indices:
        for field, options in index.items():
            try:
                ret += db.items.create_index(field, **options)
            except pymongo.errors.OperationFailure:
                if allow_rebuild and options.get("name"):
                    db.items.drop_index(options["name"])
                    ret += db.items.create_index(field, **options)

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
