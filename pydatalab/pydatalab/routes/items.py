import datetime
from typing import Callable, Dict, List, Union

from bson import ObjectId
from flask import abort, jsonify, request
from pydantic import ValidationError

from pydatalab.blocks import BLOCK_TYPES
from pydatalab.models import ITEM_MODELS, Sample
from pydatalab.mongo import flask_mongo


def reserialize_blocks(blocks_obj: Dict[str, Dict]) -> Dict[str, Dict]:
    """Create the corresponding Python objects from JSON block data, then
    serialize it again as JSON to populate any missing properties.

    Parameters:
        blocks_obj: A dictionary containing the JSON block data, keyed by block ID.

    Returns:
        A dictionary with the re-serialized block data.

    """
    for block_id, block_data in blocks_obj.items():
        blocktype = block_data["blocktype"]
        blocks_obj[block_id] = BLOCK_TYPES[blocktype].from_db(block_data).to_web()

    return blocks_obj


def dereference_files(file_ids: List[Union[str, ObjectId]]) -> Dict[str, Dict]:
    """For a list of Object IDs (as strings or otherwise), query the files collection
    and return a dictionary of the data stored under each ID.

    Parameters:
        file_ids: The list of IDs of files to return;

    Returns:
        The dereferenced data as a dictionary with (string) ID keys.

    """
    results = {
        str(f["_id"]): f
        for f in flask_mongo.db.files.find({"_id": {"$in": [ObjectId(_id) for _id in file_ids]}})
    }
    if len(results) != len(file_ids):
        raise RuntimeError(
            "Some file IDs did not have corresponding database entries.\n"
            f"Returned: {list(results.keys())}\n"
            f"Requested: {file_ids}\n"
        )

    return results


def get_starting_materials():
    items = [
        doc
        for doc in flask_mongo.db.items.aggregate(
            [
                {"$match": {"type": "starting_materials"}},
                {
                    "$project": {
                        "_id": 0,
                        "item_id": 1,
                        # "nblocks": {"$size": "$display_order"},
                        "date_acquired": 1,
                        "chemform": 1,
                        "name": 1,
                        "chemical_purity": 1,
                        "supplier": 1,
                    }
                },
            ]
        )
    ]
    return jsonify({"status": "success", "items": items})


get_starting_materials.methods = ("GET",)  # type: ignore


def get_samples():
    items = [
        doc
        for doc in flask_mongo.db.items.aggregate(
            [
                {"$match": {"type": "samples"}},
                {
                    "$project": {
                        "_id": 0,
                        "item_id": 1,
                        "sample_id": 1,
                        "nblocks": {"$size": "$display_order"},
                        "date": 1,
                        "chemform": 1,
                        "name": 1,
                    }
                },
            ]
        )
    ]
    return jsonify({"status": "success", "samples": items})


get_samples.methods = ("GET",)  # type: ignore


def search_items():
    """Perform free text search on items and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of  (default 100)
        types: If None, search all types of items. Otherwise, a list of strings
               giving the types to consider. (e.g. ["samples","starting_materials"])

    Returns:
        response list of dictionaries containing the matching items in order of
        descending match score.
    """
    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    types = request.args.get("types", default=None)
    if isinstance(types, str):
        types = types.split(",")  # should figure out how to parse as list automatically

    match_obj = {"$text": {"$search": query}}
    if types is not None:
        match_obj["type"] = {"$in": types}

    cursor = flask_mongo.db.items.aggregate(
        [
            {"$match": match_obj},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": nresults},
            {
                "$project": {
                    "_id": 0,
                    "type": 1,
                    "item_id": 1,
                    "name": 1,
                    "chemform": 1,
                }
            },
        ]
    )

    return jsonify({"status": "success", "items": list(cursor)}), 200


search_items.methods = ("GET",)  # type: ignore


def create_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    print(f"creating new samples with: {request_json}")
    item_id = request_json["item_id"]
    name = request_json["name"]
    date = request_json["date"]

    # check to make sure that item_id isn't taken already
    print("Validating item id...")
    if flask_mongo.db.items.find_one({"item_id": item_id}):
        print(f"Item ID '{item_id}' already exists in database")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "item_id_validation_error",
                }
            ),
            400,
        )
    print("Item ID is unique, and can be added to the database")

    try:
        new_sample = Sample(
            **{
                "item_id": item_id,
                "name": name,
                "date": date,
                "description": "",
                "blocks": [],  # an array of subdocuments
                "blocks_obj": {},
                "files": [],
                "file_ObjectIds": [],
                "display_order": [],  # an array of strings, which are ids for the blocks
            }
        )

    except ValidationError as error:
        return (
            jsonify(
                status="error",
                message=f"Unable to create new sample with ID {item_id}.",
                output=str(error),
            ),
            400,
        )

    result = flask_mongo.db.items.insert_one(new_sample.dict())
    if not result.acknowledged:
        return (
            jsonify(
                status="error",
                message=f"Failed to add new sample {item_id} to database.",
                output=result.raw_result,
            ),
            400,
        )

    print("sample has been added to the database")
    return (
        jsonify(
            {
                "status": "success",
                "sample_list_entry": {
                    "item_id": new_sample.item_id,
                    "nblocks": 0,
                    "date": new_sample.date,
                    "name": new_sample.name,
                },
            }
        ),
        200,
    )


create_sample.methods = ("POST",)  # type: ignore


def delete_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    item_id = request_json["item_id"]
    print(f"received request to delete sample {item_id}")

    result = flask_mongo.db.items.delete_one({"item_id": item_id})

    if result.deleted_count != 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to delete sample from database",
                }
            ),
            400,
        )
    print("Deleted successfully!")
    return (
        jsonify(
            {
                "status": "success",
            }
        ),
        200,
    )


delete_sample.methods = ("POST",)  # type: ignore


def get_item_data(item_id):
    # retrieve the entry from the databse:
    doc = flask_mongo.db.items.find_one(
        {"item_id": item_id},
    )
    if not doc:
        abort(404)

    # determine the item type and validate according to the appropriate schema
    try:
        ItemModel = ITEM_MODELS[doc["type"]]
    except KeyError as e:
        if "type" in doc:
            print(f"Item with id: {item_id} has invalid type: {doc['type']}")
        else:
            print(f"Item with id: {item_id} has no type field in document.")
        raise e

    doc = ItemModel(**doc)
    print(f"Validated item with pydantic model: {doc}")
    doc.blocks_obj = reserialize_blocks(doc.blocks_obj)

    files_data = []
    if doc.file_ObjectIds:
        files_data = dereference_files(doc.file_ObjectIds)

    return jsonify(
        {
            "status": "success",
            "item_id": item_id,
            "item_data": doc.dict(),
            "files_data": files_data,
        }
    )


get_item_data.methods = ("GET",)  # type: ignore


def save_item():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    item_id = request_json["item_id"]
    updated_data = request_json["data"]

    # These keys should not be updated here and cannot be modified by the user through this endpoint
    for k in ("_id", "file_ObjectIds"):
        if k in updated_data:
            del updated_data[k]

    updated_data["last_modified"] = datetime.datetime.now().isoformat()

    for block_id, block_data in updated_data.get("blocks_obj", {}).items():
        blocktype = block_data["blocktype"]
        block = BLOCK_TYPES[blocktype].from_web(block_data)
        updated_data["blocks_obj"][block_id] = block.to_db()

    item = flask_mongo.db.items.find_one({"item_id": item_id})

    if not item:
        return jsonify(status="error", message=f"Unable to find item: {item_id!r}."), 400

    item_type = item["type"]
    item.update(updated_data)

    try:
        item = ITEM_MODELS[item_type](**item).dict()
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update item {item_id!r} (type = {item_type}) with new data.",
                output=str(exc),
            ),
            400,
        )

    result = flask_mongo.db.items.update_one({"item_id": item_id}, {"$set": updated_data})

    if result.matched_count != 1:
        return (
            jsonify(
                status="error",
                message=f"{blocktype} Update failed. no subdocument matched",
                output=result.raw_result,
            ),
            400,
        )

    return jsonify(status="success")


save_item.methods = ("POST",)  # type: ignore

ENDPOINTS: Dict[str, Callable] = {
    "/samples/": get_samples,
    "/starting-materials/": get_starting_materials,
    "/search-items/": search_items,
    "/new-sample/": create_sample,
    "/delete-sample/": delete_sample,
    "/get-item-data/<item_id>": get_item_data,
    "/save-item/": save_item,
}
