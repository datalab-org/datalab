import contextlib
import json
import traceback
import uuid
from datetime import datetime, timedelta, timezone

import gridfs
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user
from werkzeug.exceptions import BadRequest, NotImplemented

from pydatalab.apps import BLOCK_TYPES
from pydatalab.blocks.base import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.login import get_by_id
from pydatalab.models.tasks import BlockProcessingTaskSpec, Task, TaskStage, TaskStatus, TaskType
from pydatalab.mongo import flask_mongo, get_database
from pydatalab.permissions import active_users_or_get_only, get_default_permissions
from pydatalab.scheduler import task_scheduler
from pydatalab.utils import CustomJSONEncoder

_app = None
"""Module-level reference to the Flask app, set once at blueprint registration.
Used by background tasks that need an app/request context but run outside of
a real HTTP request (e.g. APScheduler jobs).
"""


def _process_block_async(
    task_id: str, block_data: dict, event_data: dict | None, creator_id: str | None = None
):
    """Processes a block asynchronously in a background thread.

    This is the entry point for block processing jobs scheduled via APScheduler.
    It sets up a Flask app and request context so that ``current_user`` (and
    therefore ``get_default_permissions``) works within the block processing
    pipeline, even though there is no real HTTP request.

    The generated block data (which can be very large, e.g. full bokeh plots
    with embedded datasets) is written to a GridFS transfer buffer keyed by
    ``task_id``. The status endpoint reads this buffer once and deletes it on
    delivery — the GridFS data is ephemeral and only exists to bridge the async
    worker and the client's next status poll.

    Block state is also persisted to the item's ``blocks_obj`` in the normal
    way via ``_save_block_to_db``, so the GridFS data is not the source of
    truth — just the transport mechanism for the immediate response.
    """
    app_ctx = _app.app_context() if _app else contextlib.nullcontext()
    req_ctx = _app.test_request_context(method="POST") if _app else contextlib.nullcontext()

    def add_stage(message: str, level: str = "info", traceback: str | None = None):
        stage = TaskStage(
            timestamp=datetime.now(tz=timezone.utc), message=message, level=level, detail=traceback
        )
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id}, {"$push": {"spec.stages": stage.dict()}}
        )

    with app_ctx, req_ctx:
        if creator_id:
            user = get_by_id(str(creator_id))
            if user:
                login_user(user)

        try:
            LOGGER.info("Task %s: starting processing", task_id)
            flask_mongo.db.tasks.update_one(
                {"task_id": task_id}, {"$set": {"status": TaskStatus.PROCESSING}}
            )
            add_stage("Processing started")

            block_type = block_data["blocktype"]
            add_stage(f"Loading {block_type} block from database")

            block = BLOCK_TYPES[block_type].from_web(block_data)

            if event_data:
                add_stage("Processing block events")
                try:
                    block.process_events(event_data)
                except NotImplementedError:
                    pass

            add_stage("Saving block state to database")
            _save_block_to_db(block)

            add_stage("Generating visualization data")
            web_data = block.to_web()

            bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
            block_data_bytes = json.dumps(web_data, cls=CustomJSONEncoder).encode("utf-8")
            bucket.upload_from_stream(task_id, block_data_bytes)

            add_stage("Saving final results to database")
            _save_block_to_db(block)

            LOGGER.info("Task %s: completed successfully", task_id)
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
            LOGGER.exception("Task %s: failed with error: %s", task_id, e)
            add_stage(
                f"Error during processing: {str(e)}",
                level="error",
                traceback=traceback.format_exc(),
            )
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


TASK_MAX_AGE_HOURS = 6
TASK_TIMEOUT_HOURS = 1


def _cleanup_stale_tasks():
    """Periodic cleanup of stale block processing tasks and their GridFS data.

    Runs on an interval via APScheduler. Handles two cases:
    - Tasks stuck in PENDING/PROCESSING for longer than the timeout: marked as ERROR.
    - Completed/errored tasks older than the max age: deleted along with any
      associated GridFS transfer buffer data.
    """
    app_ctx = _app.app_context() if _app else contextlib.nullcontext()

    with app_ctx:
        now = datetime.now(tz=timezone.utc)
        timeout_cutoff = now - timedelta(hours=TASK_TIMEOUT_HOURS)
        age_cutoff = now - timedelta(hours=TASK_MAX_AGE_HOURS)

        # Mark timed-out tasks as errors
        timed_out = flask_mongo.db.tasks.update_many(
            {
                "type": TaskType.BLOCK_PROCESSING,
                "status": {"$in": [TaskStatus.PENDING, TaskStatus.PROCESSING]},
                "created_at": {"$lt": timeout_cutoff},
            },
            {
                "$set": {
                    "status": TaskStatus.ERROR,
                    "error_message": f"Task timed out after {TASK_TIMEOUT_HOURS} hour(s)",
                    "completed_at": now,
                }
            },
        )
        if timed_out.modified_count:
            LOGGER.warning("Marked %d timed-out block tasks as errored", timed_out.modified_count)

        # Find old completed/errored tasks to purge
        old_tasks = flask_mongo.db.tasks.find(
            {
                "type": TaskType.BLOCK_PROCESSING,
                "status": {"$in": [TaskStatus.READY, TaskStatus.ERROR]},
                "created_at": {"$lt": age_cutoff},
            },
            {"task_id": 1},
        )

        task_ids = [t["task_id"] for t in old_tasks]
        if not task_ids:
            return

        # Delete associated GridFS files
        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        deleted_files = 0
        for task_id in task_ids:
            for grid_file in bucket.find({"filename": task_id}):
                try:
                    bucket.delete(grid_file._id)
                    deleted_files += 1
                except Exception as e:
                    LOGGER.error("Error deleting GridFS file for task %s: %s", task_id, str(e))

        # Delete the task documents
        result = flask_mongo.db.tasks.delete_many(
            {"task_id": {"$in": task_ids}, "type": TaskType.BLOCK_PROCESSING}
        )

        LOGGER.info(
            "Cleaned up %d old block tasks and %d GridFS files",
            result.deleted_count,
            deleted_files,
        )


BLOCKS = Blueprint("blocks", __name__)


@BLOCKS.record_once
def _register_cleanup_job(state):
    global _app
    _app = state.app

    task_scheduler.add_periodic_job(
        func=_cleanup_stale_tasks,
        job_id="block_task_cleanup",
        hours=TASK_MAX_AGE_HOURS,
    )
    LOGGER.info("Registered block task cleanup job (every %d hours)", TASK_MAX_AGE_HOURS)


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
        }
        result = flask_mongo.db.collections.update_one(match, update)
    else:
        match = {
            "item_id": block.data["item_id"],
            f"blocks_obj.{block.block_id}": {"$exists": True},
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

    from pydatalab.config import CONFIG

    use_async = block_type in CONFIG.ASYNC_BLOCK_TYPES or getattr(
        BLOCK_TYPES[block_type], "_prefers_async", False
    )
    trigger_async = event_data and event_data.get("trigger_async", True) if event_data else True

    if block.data.get("cached"):
        use_async = False
        LOGGER.info(
            "Using synchronous processing for block %s because it is marked as cached",
            block.block_id,
        )

    if use_async and trigger_async:
        task_id = str(uuid.uuid4())

        creator_id = current_user.person.immutable_id

        LOGGER.info(
            "Scheduling asynchronous processing for block %s with task id %s",
            block.block_id,
            task_id,
        )

        block_task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=creator_id,
            status=TaskStatus.PENDING,
            spec=BlockProcessingTaskSpec(
                item_id=block_data["item_id"],
                block_id=block_data["block_id"],
                stages=[
                    TaskStage(
                        timestamp=datetime.now(tz=timezone.utc),
                        message="Task created and scheduled for asynchronous processing",
                    )
                ],
            ),
        )

        flask_mongo.db.tasks.insert_one(block_task.dict())

        task_scheduler.add_job(
            func=_process_block_async,
            args=[task_id, block_data, event_data, creator_id],
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
        if event_data:
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
            bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
            try:
                stream = bucket.open_download_stream_by_name(task_id)
                response["block_data"] = json.loads(stream.read())
                # Clean up: delete the GridFS file now that the client has the data
                bucket.delete(stream._id)
            except gridfs.errors.NoFile:
                response["block_data"] = None

    return jsonify(response), 200
