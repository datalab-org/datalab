import datetime
import json

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_login import current_user
from pydantic import ValidationError
from pymongo.results import InsertOneResult, UpdateResult

from pydatalab.config import CONFIG
from pydatalab.logger import logged_route
from pydatalab.models.collections import Collection
from pydatalab.mongo import COLLECTIONS_FTS_FIELDS, build_search_pipeline, flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions
from pydatalab.routes.v0_1.items import (
    creators_lookup,
    get_items_summary,
)

COLLECTIONS = Blueprint("collections", __name__)


@COLLECTIONS.before_request
@active_users_or_get_only
def _(): ...


@COLLECTIONS.route("/collections", methods=["GET"])
def get_collections():
    limit = request.args.get("limit", default=None, type=int)
    skip = request.args.get("skip", default=0, type=int)

    match_obj = get_default_permissions(user_only=True)

    total_count = flask_mongo.db.collections.count_documents(match_obj)

    pipeline = [{"$match": match_obj}, {"$sort": {"last_modified": -1}}]

    if skip > 0:
        pipeline.append({"$skip": skip})

    if limit is not None:
        pipeline.append({"$limit": limit})

    cursor = flask_mongo.db.collections.aggregate(pipeline)
    collections_list = [json.loads(Collection(**doc).json(exclude_unset=True)) for doc in cursor]

    return jsonify(
        {
            "status": "success",
            "data": collections_list,
            "total_count": total_count,
            "limit": limit,
            "skip": skip,
        }
    ), 200


@COLLECTIONS.route("/collections/<collection_id>", methods=["GET"])
def get_collection(collection_id):
    cursor = flask_mongo.db.collections.aggregate(
        [
            {
                "$match": {
                    "collection_id": collection_id,
                    **get_default_permissions(user_only=True),
                }
            },
            {"$lookup": creators_lookup()},
            {"$sort": {"_id": -1}},
        ]
    )

    try:
        doc = list(cursor)[0]
    except IndexError:
        doc = None

    if not doc or (not current_user.is_authenticated and not CONFIG.TESTING):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"No matching collection {collection_id=} with current authorization.",
                }
            ),
            404,
        )

    collection = Collection(**doc)

    samples = list(
        get_items_summary(
            match={
                "relationships.type": "collections",
                "relationships.immutable_id": collection.immutable_id,
            },
            project={"collections": 0},
        )
    )

    collection.num_items = len(samples)

    return jsonify(
        {
            "status": "success",
            "collection_id": collection_id,
            "data": json.loads(collection.json(exclude_unset=True)),
            "child_items": list(samples),
        }
    )


@COLLECTIONS.route("/collections", methods=["PUT"])
def create_collection():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    data = request_json.get("data", {})
    copy_from_id = request_json.get("copy_from_collection_id", None)
    starting_members = data.get("starting_members", [])

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            dict(
                status="error",
                message="Unable to create new collection without user authentication.",
                collection_id=data.get("collection_id"),
            ),
            401,
        )

    if copy_from_id:
        raise NotImplementedError("Copying collections is not yet implemented.")

    if CONFIG.TESTING:
        data["creator_ids"] = [24 * "0"]
        data["creators"] = [{"display_name": "Public testing user"}]
    else:
        data["creator_ids"] = [current_user.person.immutable_id]
        data["creators"] = [
            {
                "display_name": current_user.person.display_name,
                "contact_email": current_user.person.contact_email,
            }
        ]

    # check to make sure that item_id isn't taken already
    if flask_mongo.db.collections.find_one({"collection_id": data["collection_id"]}):
        return (
            dict(
                status="error",
                message=f"collection_id_validation_error: {data['collection_id']!r} already exists in database.",
                collection_id=data["collection_id"],
            ),
            409,  # 409: Conflict
        )

    data["last_modified"] = data.get(
        "last_modified", datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    try:
        data_model = Collection(**data)

    except ValidationError as error:
        return (
            dict(
                status="error",
                message=f"Unable to create new collection with ID {data['collection_id']}.",
                item_id=data["collection_id"],
                output=str(error),
            ),
            400,
        )

    result: InsertOneResult = flask_mongo.db.collections.insert_one(
        data_model.dict(exclude={"creators"})
    )
    if not result.acknowledged:
        return (
            dict(
                status="error",
                message=f"Failed to add new collection {data['collection_id']!r} to database.",
                collection_id=data["collection_id"],
                output=result.raw_result,
            ),
            400,
        )

    data_model.immutable_id = result.inserted_id

    errors = []
    if starting_members:
        item_ids = {d.get("item_id") for d in starting_members}
        if None in item_ids:
            item_ids.remove(None)

        results: UpdateResult = flask_mongo.db.items.update_many(
            {
                "item_id": {"$in": list(item_ids)},
                **get_default_permissions(user_only=True),
            },
            {
                "$push": {
                    "relationships": {
                        "type": "collections",
                        "immutable_id": data_model.immutable_id,
                    }
                }
            },
        )

        data_model.num_items = results.modified_count

        if results.modified_count < len(starting_members):
            errors = [
                item_id
                for item_id in starting_members
                if item_id not in results.raw_result.get("upserted", [])
            ]

    else:
        data_model.num_items = 0

    response = {
        "status": "success",
        "data": json.loads(data_model.json()),
    }

    if errors:
        response["warnings"] = [
            f"Unable to register {errors} to new collection {data_model.collection_id}"
        ]

    return (
        jsonify(response),
        201,  # 201: Created
    )


@COLLECTIONS.route("/collections/<collection_id>", methods=["PATCH"])
@logged_route
def save_collection(collection_id):
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    updated_data = request_json.get("data")

    if not updated_data:
        return (
            jsonify(
                status="error",
                message=f"Unable to find any data in request to update {collection_id=} with.",
            ),
            204,  # 204: No content
        )

    # These keys should not be updated here and cannot be modified by the user through this endpoint
    for k in ("_id", "file_ObjectIds", "creators", "creator_ids", "collection_id"):
        if k in updated_data:
            del updated_data[k]

    updated_data["last_modified"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    collection = flask_mongo.db.collections.find_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=True)}
    )

    if not collection:
        return (
            jsonify(
                status="error",
                message=f"Unable to find item with appropriate permissions and {collection_id=}.",
            ),
            400,
        )

    collection.update(updated_data)

    try:
        collection = Collection(**collection).dict()
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update item {collection_id=} with new data {updated_data}",
                output=str(exc),
            ),
            400,
        )

    result: UpdateResult = flask_mongo.db.collections.update_one(
        {"collection_id": collection_id},
        {"$set": collection},
    )

    if result.modified_count != 1:
        return (
            jsonify(
                status="error",
                message=f"Unable to update item {collection_id=} with new data {updated_data}",
                output=result.raw_result,
            ),
            400,
        )

    return jsonify(status="success"), 200


@COLLECTIONS.route("/collections/<collection_id>", methods=["DELETE"])
def delete_collection(collection_id: str):
    with flask_mongo.cx.start_session() as session:
        with session.start_transaction():
            collection_immutable_id = flask_mongo.db.collections.find_one(
                {"collection_id": collection_id, **get_default_permissions(user_only=True)},
                projection={"_id": 1},
            )["_id"]
            result = flask_mongo.db.collections.delete_one(
                {
                    "collection_id": collection_id,
                    **get_default_permissions(user_only=True, deleting=True),
                }
            )
            if result.deleted_count != 1:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"Authorization required to attempt to delete collection with {collection_id=} from the database.",
                        }
                    ),
                    401,
                )

            # If successful, remove collection from all matching items relationships
            flask_mongo.db.items.update_many(
                {
                    "relationships": {
                        "$elemMatch": {
                            "immutable_id": collection_immutable_id,
                            "type": "collections",
                        }
                    }
                },
                {
                    "$pull": {
                        "relationships": {
                            "immutable_id": collection_immutable_id,
                            "type": "collections",
                        }
                    }
                },
            )

    return (
        jsonify(
            {
                "status": "success",
            }
        ),
        200,
    )


@COLLECTIONS.route("/search-collections/", methods=["GET"])
@COLLECTIONS.route("/search/collections/", methods=["GET"])
def search_collections():
    """Perform free text search on collections and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of  (default 100)

    Returns:
        response list of dictionaries containing the matching collections in order of
        descending match score.
    """
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    skip = request.args.get("skip", default=0, type=int)

    if not query:
        return jsonify({"status": "error", "message": "No query provided."}), 400

    permissions = get_default_permissions(user_only=True)
    pipeline = build_search_pipeline(query, COLLECTIONS_FTS_FIELDS, permissions)

    count_pipeline = pipeline.copy()
    count_pipeline.append({"$count": "total"})
    count_result = list(flask_mongo.db.collections.aggregate(count_pipeline))
    total_count = count_result[0]["total"] if count_result else 0

    if skip > 0:
        pipeline.append({"$skip": skip})

    pipeline.append({"$limit": nresults})
    pipeline.append(
        {
            "$project": {
                "collection_id": 1,
                "title": 1,
            }
        }
    )

    cursor = [
        json.loads(Collection(**doc).json(exclude_unset=True))
        for doc in flask_mongo.db.collections.aggregate(pipeline)
    ]

    return jsonify(
        {
            "status": "success",
            "data": cursor,
            "total_count": total_count,
            "limit": nresults,
            "skip": skip,
        }
    ), 200


@COLLECTIONS.route("/collections/<collection_id>", methods=["POST"])
def add_items_to_collection(collection_id):
    data = request.get_json()
    refcodes = data.get("data", {}).get("refcodes", [])

    collection = flask_mongo.db.collections.find_one(
        {"collection_id": collection_id, **get_default_permissions()}
    )

    if not collection:
        return jsonify({"error": "Collection not found"}), 404

    if not refcodes:
        return jsonify({"error": "No item provided"}), 400

    item_count = flask_mongo.db.items.count_documents(
        {"refcode": {"$in": refcodes}, **get_default_permissions()}
    )

    if item_count == 0:
        return jsonify({"error": "No matching items found"}), 404

    update_result = flask_mongo.db.items.update_many(
        {"refcode": {"$in": refcodes}, **get_default_permissions()},
        {
            "$addToSet": {
                "relationships": {
                    "description": "Is a member of",
                    "relation": None,
                    "type": "collections",
                    "immutable_id": ObjectId(collection["_id"]),
                    "item_id": None,
                    "refcode": None,
                }
            }
        },
    )

    if update_result.matched_count == 0:
        return (jsonify({"status": "error", "message": "Unable to add to collection."}), 400)

    if update_result.modified_count == 0:
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "No update was performed",
                }
            ),
            200,
        )

    return (jsonify({"status": "success"}), 200)


@COLLECTIONS.route("/collections/<collection_id>/items", methods=["DELETE"])
def remove_items_from_collection(collection_id):
    data = request.get_json()
    refcodes = data.get("refcodes", [])

    collection = flask_mongo.db.collections.find_one(
        {"collection_id": collection_id, **get_default_permissions()}, projection={"_id": 1}
    )

    if not collection:
        return jsonify({"error": "Collection not found"}), 404

    if not refcodes:
        return jsonify({"error": "No refcodes provided"}), 400

    update_result = flask_mongo.db.items.update_many(
        {"refcode": {"$in": refcodes}, **get_default_permissions()},
        {
            "$pull": {
                "relationships": {
                    "immutable_id": ObjectId(collection["_id"]),
                    "type": "collections",
                }
            }
        },
    )

    if update_result.matched_count == 0:
        return jsonify({"status": "error", "message": "No matching items found."}), 404

    elif update_result.matched_count != len(refcodes):
        return jsonify(
            {
                "status": "partial-success",
                "message": f"Only {update_result.matched_count} items updated",
            }
        ), 207

    return jsonify({"status": "success", "removed_count": update_result.modified_count}), 200
