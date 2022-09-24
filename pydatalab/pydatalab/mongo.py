from typing import List, Optional

from flask_pymongo import PyMongo
from pymongo import TEXT, MongoClient
from pymongo.errors import ServerSelectionTimeoutError

flask_mongo = PyMongo()
"""This is the primary database interface used by the Flask app."""


def _get_active_mongo_client(timeoutMS: int = 100) -> MongoClient:
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
        return MongoClient(
            CONFIG.MONGO_URI,
            connectTimeoutMS=timeoutMS,
            serverSelectionTimeoutMS=timeoutMS,
            connect=True,
        )
    except ServerSelectionTimeoutError as exc:
        LOGGER.critical(f"Unable to connect to MongoDB at {CONFIG.MONGO_URI}")
        raise RuntimeError from exc


def create_default_indices(client: Optional[MongoClient] = None) -> List[str]:
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
        [(k, TEXT) for k in fts_fields],
        name="item full-text search",
        weights={"item_id": 3, "name": 3, "chemform": 3},
    )
    ret += db.items.create_index("type", name="item type")
    ret += db.items.create_index("item_id", unique=True, name="unique item ID")

    return ret


__all__ = ("flask_mongo", "create_default_indices", "_get_active_mongo_client")
