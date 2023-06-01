import datetime
import json

from flask import Blueprint, jsonify, request
from flask_login import current_user
from pydantic import ValidationError
from pymongo.results import InsertOneResult, UpdateResult

from pydatalab.config import CONFIG
from pydatalab.logger import logged_route
from pydatalab.models.collections import Collection
from pydatalab.mongo import flask_mongo
from pydatalab.routes.utils import get_default_permissions
from pydatalab.routes.v0_1.items import creators_lookup, get_samples_summary

collection = Blueprint("collections", __name__)


@collection.route("/collections/")
def get_collections():

    collections = flask_mongo.db.collections.aggregate(
        [
            {"$match": get_default_permissions(user_only=True)},
            {"$lookup": creators_lookup()},
            {"$project": {"_id": 0}},
            {"$sort": {"_id": -1}},
        ]
    )

    return jsonify({"status": "success", "data": list(collections)})


@collection.route("/collections/<collection_id>", methods=["GET"])
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
        get_samples_summary(
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


@collection.route("/collections/", methods=["PUT"])
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
        data["creators"] = [
            {"display_name": "Public testing user", "contact_email": "datalab@odbx.science"}
        ]
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

    data["date"] = data.get("date", datetime.datetime.now())

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

    immutable_id = result.inserted_id

    errors = []
    if starting_members:
        item_ids = set(d.get("item_id") for d in starting_members)
        if None in item_ids:
            item_ids.remove(None)

        results: UpdateResult = flask_mongo.db.items.update_many(
            {
                "item_id": {"$in": list(item_ids)},
                **get_default_permissions(user_only=True),
            },
            {"$push": {"relationships": {"type": "collections", "immutable_id": immutable_id}}},
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


@collection.route("/collections/<collection_id>", methods=["PATCH"])
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

    updated_data["last_modified"] = datetime.datetime.now().isoformat()

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


@collection.route("/collections/<collection_id>", methods=["DELETE"])
def delete_collection(collection_id: str):

    result = flask_mongo.db.collections.delete_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=True)}
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
    return (
        jsonify(
            {
                "status": "success",
            }
        ),
        200,
    )


@collection.route("/search-collections/", methods=["GET"])
def search_collections():
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)

    match_obj = {"$text": {"$search": query}, **get_default_permissions(user_only=True)}

    cursor = [
        json.loads(Collection(**doc).json(exclude_unset=True))
        for doc in flask_mongo.db.collections.aggregate(
            [
                {"$match": match_obj},
                {"$sort": {"score": {"$meta": "textScore"}}},
                {"$limit": nresults},
                {
                    "$project": {
                        "collection_id": 1,
                        "title": 1,
                    }
                },
            ]
        )
    ]

    return jsonify({"status": "success", "data": list(cursor)}), 200
