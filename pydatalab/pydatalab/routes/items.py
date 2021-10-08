import datetime
from typing import Callable, Dict, List, Union

from bson import ObjectId
from flask import abort, jsonify, request
from pydantic import ValidationError

from pydatalab.blocks import BLOCK_KINDS
from pydatalab.models import Sample, StartingMaterial
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
        blocks_obj[block_id] = BLOCK_KINDS[blocktype].from_db(block_data).to_web()

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
    cursor = [
        StartingMaterial(**doc).dict()
        for doc in flask_mongo.db.data.aggregate(
            [
                {"$match": {"type": "starting_materials"}},
                {
                    "$project": {
                        "_id": 0,
                        "item_id": 1,
                        # "nblocks": {"$size": "$display_order"},
                        "date_aquired": 1,
                        "chemform": 1,
                        "name": 1,
                        "chemical_purity": 1,
                        "supplier": 1,
                    }
                },
            ]
        )
    ]
    return jsonify({"status": "success", "items": cursor})


def get_samples():
    cursor = [
        # Sample(**doc).dict() # disabling pydantic type checking since it would require returning more fields from mongodb
        doc
        for doc in flask_mongo.db.data.aggregate(
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
    return jsonify({"status": "success", "samples": cursor})


get_samples.methods = ("GET",)  # type: ignore


def create_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    print(f"creating new samples with: {request_json}")
    sample_id = request_json["sample_id"]
    name = request_json["name"]
    date = request_json["date"]

    # check to make sure that sample_id isn't taken already
    print("Validating sample id...")
    if flask_mongo.db.data.find_one({"sample_id": sample_id}):
        print(f"Sample ID '{sample_id}' already exists in database")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "sample_id_validation_error",
                }
            ),
            400,
        )
    print("Sample ID is unique, and can be added to the database")

    try:
        new_sample = Sample(
            **{
                "sample_id": sample_id,
                "item_id": sample_id,
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

    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to create new sample with ID {sample_id}.",
                output=str(exc),
            ),
            400,
        )

    result = flask_mongo.db.data.insert_one(new_sample.dict())
    if not result.acknowledged:
        return (
            jsonify(
                status="error",
                message=f"Failed to add new sample {sample_id} to database.",
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
                    "sample_id": new_sample.sample_id,
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
    sample_id = request_json["sample_id"]
    print(f"received request to delete sample {sample_id}")

    result = flask_mongo.db.data.delete_one({"sample_id": sample_id})

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


def get_sample_data(sample_id):
    # retrieve the entry from the databse:
    doc = flask_mongo.db.data.find_one(
        {"sample_id": sample_id},
    )
    if not doc:
        abort(404)

    doc = Sample(**doc)

    doc.blocks_obj = reserialize_blocks(doc.blocks_obj)

    files_data = []
    if doc.file_ObjectIds:
        files_data = dereference_files(doc.file_ObjectIds)

    return jsonify(
        {
            "status": "success",
            "sample_id": sample_id,
            "sample_data": doc.dict(),
            "files_data": files_data,
        }
    )


get_sample_data.methods = ("GET",)  # type: ignore


def save_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    sample_id = request_json["sample_id"]
    updated_data = request_json["data"]

    # These keys should not be updated here and cannot be modified by the user through this endpoint
    for k in ("_id", "file_ObjectIds"):
        if k in updated_data:
            del updated_data[k]

    updated_data["last_modified"] = datetime.datetime.now().isoformat()

    for block_id, block_data in updated_data.get("blocks_obj", {}).items():
        blocktype = block_data["blocktype"]
        block = BLOCK_KINDS[blocktype].from_web(block_data)
        updated_data["blocks_obj"][block_id] = block.to_db()

    sample = flask_mongo.db.data.find_one({"sample_id": sample_id})
    if not sample:
        (jsonify(status="error", message=f"Unable to find sample {sample_id!r}."), 400)

    sample.update(updated_data)
    try:
        sample = Sample(**sample).dict()
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update sample {sample_id!r} with new data.",
                output=str(exc),
            ),
            400,
        )

    result = flask_mongo.db.data.update_one({"sample_id": sample_id}, {"$set": updated_data})

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


save_sample.methods = ("POST",)  # type: ignore

ENDPOINTS: Dict[str, Callable] = {
    "/samples/": get_samples,
    "/starting-materials/": get_starting_materials,
    "/new-sample/": create_sample,
    "/delete-sample/": delete_sample,
    "/get_sample_data/<sample_id>": get_sample_data,
    "/save-sample/": save_sample,
}
