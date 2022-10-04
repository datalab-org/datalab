from typing import List, Optional

# Must be imported in this way to allow for easy patching with mongomock
import pymongo
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure

__all__ = (
    "flask_mongo",
    "check_mongo_connection",
    "create_default_indices",
    "_get_active_mongo_client",
)

flask_mongo = PyMongo()
"""This is the primary database interface used by the Flask app."""


def _get_active_mongo_client(timeoutMS: int = 100) -> pymongo.MongoClient:
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


def create_default_indices(client: Optional[pymongo.MongoClient] = None) -> List[str]:
    """Creates indices for the configured or passed MongoClient.

    Indexes created are:
        - A text index over all string fields in item models,
        - An index over item type,
        - A unique index over `item_id`.

    Returns:
        A list of messages returned by each `create_index` call.

    """
    from pydatalab.models import ITEM_MODELS

    if client is None:
        client = _get_active_mongo_client()
    db = client.get_database()

    fts_fields = set()
    for model in ITEM_MODELS:
        schema = ITEM_MODELS[model].schema()
        for f in schema["properties"]:
            if schema["properties"][f]["type"] == "string":
                fts_fields.add(f)

    ret = []

    ret += db.items.create_index(
        [(k, pymongo.TEXT) for k in fts_fields],
        name="item full-text search",
        weights={"item_id": 3, "name": 3, "chemform": 3},
    )
    ret += db.items.create_index("type", name="item type")
    ret += db.items.create_index("item_id", unique=True, name="unique item ID")

    return ret
