from typing import Callable, Dict

from flask import jsonify, request

from pydatalab.blocks import BLOCK_KINDS
from pydatalab.mongo import flask_mongo


# TODO: add input data validation
def add_data_block():
    """Call with AJAX to add a block to the sample"""

    request_json = request.get_json()

    # pull out required arguments from json
    sample_id = request_json["sample_id"]
    block_type = request_json["block_kind"]
    insert_index = request_json["index"]

    print(f"Adding a block of type: {block_type} to sample: {sample_id}")
    if block_type not in BLOCK_KINDS:
        return jsonify(status="error", message="Invalid block type"), 400

    block = BLOCK_KINDS[block_type](sample_id=sample_id)

    data = block.to_db()
    # print("updating the database with:")
    # print(sample_id)
    # print(data)
    # print(insert_index)

    # currently, adding to both blocks and blocks_obj to mantain compatibility with
    # the old site. The new site only uses blocks_obj
    if insert_index:
        display_order_update = {
            "$each": [block.block_id],
            "$position": insert_index,
        }
    else:
        display_order_update = block.block_id

    result = flask_mongo.db.data.update_one(
        {"sample_id": sample_id},
        {
            "$push": {"blocks": data, "display_order": display_order_update},
            "$set": {f"blocks_obj.{block.block_id}": data},
        },
    )

    print(result.raw_result)
    if result.modified_count < 1:
        return (
            jsonify(
                status="error",
                message="Update failed. The sample_id probably incorrect: {}".format(sample_id),
            ),
            400,
        )

    # get the new display_order:
    display_order_result = flask_mongo.db.data.find_one(
        {"sample_id": sample_id}, {"display_order": 1}
    )
    print("new document: {}".format(display_order_result))

    return jsonify(
        status="success",
        new_block_obj=block.to_web(),
        new_display_order=display_order_result["display_order"],
    )


add_data_block.methods = ("POST",)  # type: ignore


def update_block():
    """Take in json block data from site, process, and spit
    out updated data. May be used, for example, when the user
    changes plot parameters and the server needs to generate a new
    plot
    """
    request_json = request.get_json()
    print("update_block called with : " + str(request_json)[:1000])
    block_data = request_json["block_data"]
    blocktype = block_data["blocktype"]

    block = BLOCK_KINDS[blocktype].from_web(block_data)

    return jsonify(status="success", new_block_data=block.to_web()), 200


update_block.methods = ("POST",)  # type: ignore


def delete_block():
    """Completely delete a data block fron the database. In the future,
    we may consider preserving data by moving it to a different array,
    or simply making it invisible"""
    request_json = request.get_json()
    sample_id = request_json["sample_id"]
    block_id = request_json["block_id"]

    # print(update)
    result = flask_mongo.db.data.update_one(
        {"sample_id": sample_id},
        {
            "$pull": {
                "blocks": {"block_id": block_id},
                "display_order": block_id,
            },
            "$unset": {f"blocks_obj.{block_id}": ""},
        },
    )

    print("Removing block: {} , from sample: {}".format(block_id, sample_id))
    print("result:")
    print(result.raw_result)

    if result.modified_count < 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Update failed. The sample_id probably incorrect: {}".format(
                        sample_id
                    ),
                }
            ),
            400,
        )
    return (
        jsonify({"status": "success"}),
        200,
    )  # could try to switch to http 204 is "No Content" success with no json


delete_block.methods = ("POST",)  # type: ignore

ENDPOINTS: Dict[str, Callable] = {
    "/add-data-block": add_data_block,
    "/update-block": update_block,
    "/delete-block": delete_block,
}
