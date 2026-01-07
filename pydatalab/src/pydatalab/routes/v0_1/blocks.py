import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest, NotImplemented

from pydatalab.apps import BLOCK_TYPES
from pydatalab.blocks.base import DataBlock
from pydatalab.config import CONFIG
from pydatalab.models.tasks import BlockProcessingTaskSpec, Task, TaskStage, TaskStatus, TaskType
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions
from pydatalab.scheduler import export_scheduler


def _process_block_async_internal(task_id: str, block_data: dict, event_data: dict | None):
    def add_stage(message: str, level: str = "info"):
        stage = TaskStage(timestamp=datetime.now(tz=timezone.utc), message=message, level=level)
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id}, {"$push": {"spec.stages": stage.dict()}}
        )

    try:
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id}, {"$set": {"status": TaskStatus.PROCESSING}}
        )
        add_stage("Processing started")

        block_type = block_data["blocktype"]
        add_stage(f"Loading {block_type} block from database")

        block = BLOCK_TYPES[block_type].from_web(block_data)

        if event_data and not event_data.get("trigger_async", False):
            add_stage("Processing block events")
            try:
                block.process_events(event_data)
            except NotImplementedError:
                pass

        add_stage("Saving block state to database")
        _save_block_to_db(block)

        add_stage("Generating visualization data")
        block.to_web()

        add_stage("Saving final results to database")
        _save_block_to_db(block)

        add_stage("Processing completed successfully", level="info")
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.READY,
                    "completed_at": datetime.now(tz=timezone.utc),
                }
            },
        )

    except Exception as e:
        add_stage(f"Error during processing: {str(e)}", level="error")
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.ERROR,
                    "error_message": str(e),
                    "completed_at": datetime.now(tz=timezone.utc),
                }
            },
        )


def _process_block_async(task_id: str, block_data: dict, event_data: dict | None, app):
    if app is not None:
        with app.app_context():
            _process_block_async_internal(task_id, block_data, event_data)
    else:
        _process_block_async_internal(task_id, block_data, event_data)


BLOCKS = Blueprint("blocks", __name__)


@BLOCKS.before_request
@active_users_or_get_only
def _(): ...


@BLOCKS.route("/add-data-block/", methods=["POST"])
@BLOCKS.route("/blocks/", methods=["PUT"])
def add_data_block():
    """Call with AJAX to add a block to the sample"""

    request_json = request.get_json()

    # pull out required arguments from json
    block_type = request_json["block_type"]
    item_id = request_json["item_id"]
    insert_index = request_json["index"]

    if block_type not in BLOCK_TYPES:
        raise NotImplemented(  # noqa
            f"Invalid block type {block_type!r}, must be one of {BLOCK_TYPES.keys()}"
        )

    block = BLOCK_TYPES[block_type](item_id=item_id)

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
            "$push": {"display_order": display_order_update},
            "$set": {f"blocks_obj.{block.block_id}": block.to_db()},
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
        raise NotImplemented(  # noqa
            f"Invalid block type {block_type!r}, must be one of {BLOCK_TYPES.keys()}"
        )

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


def _save_block_to_db(block: DataBlock):
    """Save data for a single block within an item to the database,
    overwriting previous data saved there.

    Parameters:
        block: The instance of DataBlock to save.

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

    result = flask_mongo.db.items.update_one(match, update)

    if result.matched_count != 1:
        raise BadRequest(
            f"Failed to save block, likely because item_id ({block.data.get('item_id')}), collection_id ({block.data.get('collection_id')}) and/or block_id ({block.block_id}) wasn't found"
        )


@BLOCKS.route("/update-block/", methods=["POST"])
@BLOCKS.route("/blocks/", methods=["POST"])
def update_block():
    """Updates the server-side data block based on received JSON, including triggering
    any events associated with the given block type.

    """

    request_json = request.get_json()
    block_data = request_json["block_data"]
    event_data = request_json.get("event_data", None)

    block_type = block_data["blocktype"]

    if block_type not in BLOCK_TYPES:
        raise NotImplemented(  # noqa: F901
            f"Invalid block type {block_type!r}, must be one of {BLOCK_TYPES.keys()}"
        )

    block = BLOCK_TYPES[block_type].from_web(block_data)

    prefers_async = getattr(BLOCK_TYPES[block_type], "prefers_async", False)
    trigger_async = event_data and event_data.get("trigger_async", False) if event_data else False

    if prefers_async and trigger_async:
        task_id = str(uuid.uuid4())

        if not CONFIG.TESTING:
            creator_id = str(current_user.person.immutable_id)
        else:
            creator_id = "000000000000000000000000"

        block_task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=creator_id,
            status=TaskStatus.PENDING,
            spec=BlockProcessingTaskSpec(
                item_id=block_data["item_id"],
                block_id=block_data["block_id"],
            ),
        )

        flask_mongo.db.tasks.insert_one(block_task.dict())

        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = None

        export_scheduler.add_job(
            func=_process_block_async,
            args=[task_id, block_data, event_data, app],
            job_id=task_id,
        )

        return (
            jsonify(
                status="success",
                processing_async=True,
                task_id=task_id,
                status_url=f"/blocks/{task_id}/status",
            ),
            202,
        )
    else:
        if event_data and not event_data.get("trigger_async", False):
            try:
                block.process_events(event_data)
            except NotImplementedError:
                pass

        # Save state from UI
        _save_block_to_db(block)

        # Reload the block with new UI state
        new_block_data = block.to_web()

        # Save results to DB
        _save_block_to_db(block)

        return (
            jsonify(status="success", saved_successfully=True, new_block_data=new_block_data),
            200,
        )


@BLOCKS.route("/delete-block/", methods=["POST"])
@BLOCKS.route("/blocks/", methods=["DELETE"])
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


@BLOCKS.route("/blocks/<string:task_id>/status", methods=["GET"])
def get_block_task_status(task_id: str):
    task = flask_mongo.db.tasks.find_one({"task_id": task_id, "type": TaskType.BLOCK_PROCESSING})

    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404

    response = {
        "status": task["status"],
        "task_id": task_id,
        "created_at": task["created_at"],
    }

    if task.get("spec", {}).get("stages"):
        response["stages"] = task["spec"]["stages"]
    if task.get("completed_at"):
        response["completed_at"] = task["completed_at"]
    if task.get("error_message"):
        response["error_message"] = task["error_message"]

    if task["status"] == TaskStatus.READY:
        item_id = task["spec"]["item_id"]
        block_id = task["spec"]["block_id"]

        item = flask_mongo.db.items.find_one(
            {"item_id": item_id, **get_default_permissions(user_only=False)},
            {f"blocks_obj.{block_id}": 1},
        )

        if item and "blocks_obj" in item and block_id in item["blocks_obj"]:
            block_data_from_db = item["blocks_obj"][block_id]
            block_type = block_data_from_db["blocktype"]

            block = BLOCK_TYPES[block_type].from_web(block_data_from_db)
            response["block_data"] = block.to_web()

    return jsonify(response), 200
