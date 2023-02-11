from typing import Callable, Dict

from flask import jsonify
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.models.collections import Collection
from pydatalab.mongo import flask_mongo
from pydatalab.routes.utils import get_default_permissions
from pydatalab.routes.v0_1.items import creators_lookup, get_samples_summary


def get_collections():

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                status="error",
                message="Authorization required to list collections.",
            ),
            401,
        )

    collections = flask_mongo.db.collections.aggregate(
        [
            {"$match": get_default_permissions(user_only=True)},
            {"$lookup": creators_lookup()},
            {"$project": {"_id": 0}},
            {"$sort": {"_id": -1}},
        ]
    )
    return jsonify({"status": "success", "collections": list(collections)})


def get_collection(collection_id):

    collection = flask_mongo.db.collections.aggregate(
        [
            {
                "$match": {
                    "collection_id": collection_id,
                    **get_default_permissions(user_only=False),
                }
            },
            {"$lookup": creators_lookup()},
            {"$sort": {"_id": -1}},
        ]
    )

    collection = Collection(**list(collection)[0])

    samples = get_samples_summary(
        match={
            "relationships.type": "collection",
            "relationships.immutable_id": collection.immutable_id,
        }
    )

    return jsonify({"status": "success", "samples": list(samples)})


ENDPOINTS: Dict[str, Callable] = {
    "/collections/": get_collections,
    "/collections/<collection_id>": get_collection,
}
