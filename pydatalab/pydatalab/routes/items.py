import datetime
from typing import Callable, Dict, List, Union

from bson import ObjectId
from flask import abort, jsonify, request
from pydantic import ValidationError

from pydatalab.blocks import BLOCK_TYPES

# from pydatalab.logger import LOGGER
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
        blocks_obj[block_id] = (
            BLOCK_TYPES.get(blocktype, BLOCK_TYPES["notsupported"]).from_db(block_data).to_web()
        )

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
    schema = Sample.schema()
    missing_keys = set()
    for k in schema["required"]:
        if k not in request_json:
            missing_keys.add(k)

    if missing_keys:
        raise ValidationError(
            f"Request to create sample was thwarted by the lack of required key(s): {missing_keys}"
        )

    new_sample = {k: request_json[k] for k in schema["properties"] if k in request_json}

    # check to make sure that item_id isn't taken already
    if flask_mongo.db.items.find_one({"item_id": request_json["item_id"]}):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"item_id_validation_error: {request_json['item_id']!r} already exists in database.",
                }
            ),
            409,  # 409: Conflict
        )

    new_sample["date"] = new_sample.get("date", datetime.datetime.now())
    try:
        new_sample = Sample(**new_sample)

    except ValidationError as error:
        return (
            jsonify(
                status="error",
                message=f"Unable to create new sample with ID {new_sample['item_id']}.",
                output=str(error),
            ),
            400,
        )

    result = flask_mongo.db.items.insert_one(new_sample.dict())
    if not result.acknowledged:
        return (
            jsonify(
                status="error",
                message=f"Failed to add new sample {new_sample.item_id!r} to database.",
                output=result.raw_result,
            ),
            400,
        )

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
        201,  # 201: Created
    )


create_sample.methods = ("POST",)  # type: ignore


def delete_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    item_id = request_json["item_id"]

    result = flask_mongo.db.items.delete_one({"item_id": item_id})

    if result.deleted_count != 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to delete sample with {item_id=} from the database.",
                }
            ),
            400,
        )
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
    except KeyError:
        if "type" in doc:
            raise KeyError(f"Item {item_id=} has invalid type: {doc['type']}")
        else:
            raise KeyError(f"Item {item_id=} has no type field in document.")

    doc = ItemModel(**doc)
    doc.blocks_obj = reserialize_blocks(doc.blocks_obj)

    files_data = []
    if doc.file_ObjectIds:
        files_data = dereference_files(doc.file_ObjectIds)

    # find any documents with relationships that mention this document

    # option 1: use projection (will need post-processing)
    incoming_relationships = flask_mongo.db.items.find(
        {"item_id": doc.item_id},
        {"item_id": 1, "relationships": {"$elemMatch": {"item_id": doc.item_id}}},
    )

    # option 2: use an aggregation pipeline:
    # incoming_relationships = flask_mongo.db.items.aggregate(
    #    [
    #        {"$match": {"relationships.item_id": doc.item_id}},
    #        {"$project": {"item_id": 1, "name": 1, "type": 1, "relationship": "$relationships"}},
    #        {"$unwind": "$relationship"},
    #        {"$match": {"relationship.item_id": doc.item_id}},
    #    ]
    # )

    # temporary hack: front end currently expects legacy parent_items and child_items fields,
    # so generate them on the fly after passing through the model.
    return_dict = doc.dict()

    return_dict["parent_items"] = [d["item_id"] for d in return_dict["relationships"]]
    return_dict["child_items"] = [d["item_id"] for d in incoming_relationships]

    return jsonify(
        {
            "status": "success",
            "item_id": item_id,
            "item_data": return_dict,
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

        block = BLOCK_TYPES.get(blocktype, BLOCK_TYPES["notsupported"]).from_web(block_data)

        updated_data["blocks_obj"][block_id] = block.to_db()

    item = flask_mongo.db.items.find_one({"item_id": item_id})

    if not item:
        return (
            jsonify(status="error", message=f"Unable to find item with {item_id=}."),
            400,
        )

    item_type = item["type"]
    item.update(updated_data)

    try:
        item = ITEM_MODELS[item_type](**item).dict()
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update item {item_id=} ({item_type=}) with new data {updated_data}",
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


# def get_graph(item_id, depth=3):
#     """Generate a graph in cytoscape.js format centered around the item_id specified"""

#     nodes = []
#     edges = []
#     visited_ids = {}

#     def _recursive_graph_search(item_id, depth, nodes, edges, visited_ids):
#         LOGGER.debug(f"_recursive_graph_search called with {item_id=}")

#         root = flask_mongo.db.items.find_one(
#             {"item_id": item_id}, {"item_id": 1, "relationships": 1, "name": 1, "type": 1}
#         )

#         nodes.append(
#             {
#                 "data": {
#                     "id": item_id,
#                     "name": root["name"],
#                     "type": root["type"],
#                 }
#             }
#         )

#         visited_ids.add(item_id)

#         if depth == 0:
#             return

#         for parent_relationship in root["relationships"]:
#             if parent_relationship["item_id"] in visited_ids:
#                 continue

#             edges.append({"data": { "id": }})
#             _recursive_graph_search(
#                 parent_relationship["item_id"], depth - 1, nodes, edges, visited_ids
#             )

#         return [
#             _recursive_graph_search(d["item"]["item_id"], depth=depth - 1)
#             for d in parents["synthesis_constituents"]
#         ]

#     # children = flask_mongo.db.items.find(
#     # {"synthesis_constituents.item.item_id": item_id}, {"item_id": 1}
#     # )
#     return jsonify(_recursive_graph_search(item_id, depth))
#     # return jsonify([parents, list(children)])


# get_graph.methods = ("GET",)  # type: ignore


ENDPOINTS: Dict[str, Callable] = {
    "/samples/": get_samples,
    "/starting-materials/": get_starting_materials,
    "/search-items/": search_items,
    "/new-sample/": create_sample,
    "/delete-sample/": delete_sample,
    "/get-item-data/<item_id>": get_item_data,
    "/save-item/": save_item,
    # "/get-graph/<item_id>": get_graph,
}
