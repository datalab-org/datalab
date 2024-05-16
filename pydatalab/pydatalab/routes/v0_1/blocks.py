import pymongo.errors
from flask import Blueprint, jsonify, request

from pydatalab.blocks import BLOCK_TYPES
from pydatalab.blocks.base import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions

BLOCKS = Blueprint("blocks", __name__)


@BLOCKS.before_request
@active_users_or_get_only
def _(): ...


@BLOCKS.route("/add-data-block/", methods=["POST"])
def add_data_block():
    """Call with AJAX to add a block to the sample"""

    request_json = request.get_json()

    # pull out required arguments from json
    block_type = request_json["block_type"]
    item_id = request_json["item_id"]
    insert_index = request_json["index"]

    if block_type not in BLOCK_TYPES:
        return jsonify(status="error", message="Invalid block type"), 400

    block = BLOCK_TYPES[block_type](item_id=item_id)

    data = block.to_db()

    # currently, adding to both blocks and blocks_obj to mantain compatibility with
    # the old site. The new site only uses blocks_obj
    if insert_index:
        display_order_update = {
            "$each": [block.block_id],
            "$position": insert_index,
        }
    else:
        display_order_update = block.block_id

    result = flask_mongo.db.items.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {
            "$push": {"blocks": data, "display_order": display_order_update},
            "$set": {f"blocks_obj.{block.block_id}": data},
        },
    )

    if result.modified_count < 1:
        return (
            jsonify(
                status="error",
                message=f"Update failed. {item_id=} is probably incorrect.",
            ),
            400,
        )

    # get the new display_order:
    display_order_result = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)}, {"display_order": 1}
    )

    return jsonify(
        status="success",
        new_block_obj=block.to_web(),
        new_block_insert_index=insert_index
        if insert_index is None
        else len(display_order_result["display_order"]) - 1,
        new_display_order=display_order_result["display_order"],
    )


@BLOCKS.route("/add-collection-data-block/", methods=["POST"])
def add_collection_data_block():
    """Call with AJAX to add a block to the collection."""

    request_json = request.get_json()

    # pull out required arguments from json
    block_type = request_json["block_type"]
    collection_id = request_json["collection_id"]
    insert_index = request_json["index"]

    if block_type not in BLOCK_TYPES:
        return jsonify(status="error", message="Invalid block type"), 400

    block = BLOCK_TYPES[block_type](collection_id=collection_id)

    data = block.to_db()

    # currently, adding to both blocks and blocks_obj to mantain compatibility with
    # the old site. The new site only uses blocks_obj
    if insert_index:
        display_order_update = {
            "$each": [block.block_id],
            "$position": insert_index,
        }
    else:
        display_order_update = block.block_id

    result = flask_mongo.db.collections.update_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=True)},
        {
            "$push": {"blocks": data, "display_order": display_order_update},
            "$set": {f"blocks_obj.{block.block_id}": data},
        },
    )

    if result.modified_count < 1:
        return (
            jsonify(
                status="error",
                message=f"Update failed. {collection_id=} is probably incorrect.",
            ),
            400,
        )

    # get the new display_order:
    display_order_result = flask_mongo.db.collections.find_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=True)},
        {"display_order": 1},
    )

    return jsonify(
        status="success",
        new_block_obj=block.to_web(),
        new_block_insert_index=insert_index
        if insert_index is None
        else len(display_order_result["display_order"]) - 1,
        new_display_order=display_order_result["display_order"],
    )


def _save_block_to_db(block: DataBlock) -> bool:
    """Save data for a single block within an item to the database,
    overwriting previous data saved there.
    returns true if successful, false if unsuccessful
    """
    updated_block = block.to_db()
    update = {"$set": {f"blocks_obj.{block.block_id}": updated_block}}

    if block.data.get("collection_id"):
        match = {
            "collection_id": block.data["collection_id"],
            f"blocks_obj.{block.block_id}": {"$exists": True},
            **get_default_permissions(user_only=False),
        }
    else:
        match = {
            "item_id": block.data["item_id"],
            f"blocks_obj.{block.block_id}": {"$exists": True},
            **get_default_permissions(user_only=False),
        }

    try:
        result = flask_mongo.db.items.update_one(match, update)
    except pymongo.errors.DocumentTooLarge:
        LOGGER.warning(
            "DocumentTooLarge error occurred while saving block to db, block.block_id='%s'",
            block.block_id,
        )
        return False

    if result.matched_count != 1:
        LOGGER.warning(
            f"_save_block_to_db failed, likely because item_id ({block.data.get('item_id')}), collection_id ({block.data.get('collection_id')}) and/or block_id ({block.block_id}) wasn't found"
        )
        return False
    else:
        return True


@BLOCKS.route("/update-block/", methods=["POST"])
def update_block():
    """Take in json block data from site, process, and spit
    out updated data. May be used, for example, when the user
    changes plot parameters and the server needs to generate a new
    plot.
    """

    request_json = request.get_json()
    block_data = request_json["block_data"]
    blocktype = block_data["blocktype"]
    save_to_db = request_json.get("save_to_db", False)

    block = BLOCK_TYPES[blocktype].from_web(block_data)

    saved_successfully = False
    if save_to_db:
        saved_successfully = _save_block_to_db(block)

    return (
        jsonify(
            status="success", saved_successfully=saved_successfully, new_block_data=block.to_web()
        ),
        200,
    )


@BLOCKS.route("/delete-block/", methods=["POST"])
def delete_block():
    """Completely delete a data block from the database. In the future,
    we may consider preserving data by moving it to a different array,
    or simply making it invisible"""
    request_json = request.get_json()
    item_id = request_json["item_id"]
    block_id = request_json["block_id"]

    result = flask_mongo.db.items.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {
            "$pull": {
                "blocks": {"block_id": block_id},
                "display_order": block_id,
            },
            "$unset": {f"blocks_obj.{block_id}": ""},
        },
    )

    if result.modified_count < 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Update failed. The item_id probably incorrect: {item_id}",
                }
            ),
            400,
        )
    return (
        jsonify({"status": "success"}),
        200,
    )  # could try to switch to http 204 is "No Content" success with no json


@BLOCKS.route("/delete-collection-block/", methods=["POST"])
def delete_collection_block():
    """Completely delete a data block from the database that is currently
    attached to a collection.

    In the future, we may consider preserving data by moving it to a different array,
    or simply making it invisible"""
    request_json = request.get_json()
    collection_id = request_json["collection_id"]
    block_id = request_json["block_id"]

    result = flask_mongo.db.collections.update_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=True)},
        {
            "$pull": {
                "blocks": {"block_id": block_id},
                "display_order": block_id,
            },
            "$unset": {f"blocks_obj.{block_id}": ""},
        },
    )

    if result.modified_count < 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Update failed. The collection_id probably incorrect: {collection_id}",
                }
            ),
            400,
        )
    return (
        jsonify({"status": "success"}),
        200,
    )
