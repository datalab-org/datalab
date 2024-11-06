from typing import List, Optional
import collections

# Must be imported in this way to allow for easy patching with mongomock
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
            if (p.get("type") == "string" and p.get("format") not in ("date-time", "uuid"))
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
) -> List[str]:
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


def create_ngram_item_index(
    client: Optional[pymongo.MongoClient] = None,
    background: bool = False,
    filter_top_ngrams: float | None = 0.5,
    target_index_name: str = "ngram_fts_index",
):
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

    # construct manual ngram index
    ngram_index = {}
    item_count: int = 0
    global_ngram_count = collections.defaultdict(int)
    for item in db.items.find({}):
        item_count += 1
        ngrams = _generate_item_ngrams(item, item_fts_fields)
        ngram_index[item["_id"]] = list(ngrams)
        for g in ngrams:
            global_ngram_count[g] += ngrams[g]

    # filter out common ngrams that are found in filter_top_ngrams proportion of entries
    if filter_top_ngrams is not None:
        for ngram in global_ngram_count:
            if global_ngram_count[ngram] / item_count > filter_top_ngrams:
                for item in ngram_index:
                    ngram_index[item].pop(ngram, None)

    for _id, item in ngram_index.items():
        db.items.update_one({"_id": _id}, {"$set": {"_fts_ngrams": item}})

    try:
        result = db.items.create_index("_fts_ngrams", name=target_index_name, background=background)
    except pymongo.errors.OperationFailure:
        db.users.drop_index(target_index_name)
        result = db.items.create_index("_fts_ngrams", name=target_index_name, background=background)

    return result

def _generate_ngrams(value, n: int = 3) -> dict[str, int]:
    import re

    ngrams = collections.defaultdict(
        int,
    )
    if len(value) < n:
        return ngrams

    # first, split by whitespace and punctuation
    tokenized_value = re.split(r"[\s,.:?!=-_]", value)

    # then loop over tokens and ngrammify
    for value in tokenized_value:
        if len(value) < n:
            continue
        for v in ("".join(value[i : i + n].lower()) for i in range(len(value) - (n - 1))):
            ngrams[v] += 1

    return ngrams

def _generate_item_ngrams(item, fts_fields):
    ngrams = collections.defaultdict(int)
    for field in fts_fields:
        field_ngrams = _generate_ngrams(item.get(field, None))
        for k in field_ngrams:
            ngrams[k] += field_ngrams[k]

    return ngrams

