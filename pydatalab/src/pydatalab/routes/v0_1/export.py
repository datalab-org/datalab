import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, send_file
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.export_utils import create_eln_file
from pydatalab.models.export_task import ExportStatus, ExportTask
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only

EXPORT = Blueprint("export", __name__)


@EXPORT.before_request
@active_users_or_get_only
def _(): ...


def _generate_export_in_background(task_id: str, collection_id: str):
    """Background function to generate the .eln file.

    Parameters:
        task_id: ID of the export task
        collection_id: ID of the collection to export
    """
    try:
        flask_mongo.db.export_tasks.update_one(
            {"task_id": task_id}, {"$set": {"status": ExportStatus.PROCESSING}}
        )

        export_dir = Path(CONFIG.FILE_DIRECTORY) / "exports"
        export_dir.mkdir(exist_ok=True)

        output_path = export_dir / f"{task_id}.eln"
        create_eln_file(collection_id, str(output_path))

        flask_mongo.db.export_tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": ExportStatus.READY,
                    "file_path": str(output_path),
                    "completed_at": datetime.now(tz=timezone.utc),
                }
            },
        )

    except Exception as e:
        flask_mongo.db.export_tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": ExportStatus.ERROR,
                    "error_message": str(e),
                    "completed_at": datetime.now(tz=timezone.utc),
                }
            },
        )


@EXPORT.route("/collections/<string:collection_id>/export", methods=["POST"])
def start_collection_export(collection_id: str):
    """Start exporting a collection to .eln format.

    Parameters:
        collection_id: The collection ID to export

    Returns:
        JSON response with task_id and status_url
    """

    collection = flask_mongo.db.collections.find_one({"collection_id": collection_id})
    if not collection:
        return jsonify({"status": "error", "message": f"Collection {collection_id} not found"}), 404

    task_id = str(uuid.uuid4())

    if not CONFIG.TESTING:
        creator_id = current_user.person.immutable_id
    else:
        creator_id = "000000000000000000000000"

    export_task = ExportTask(
        task_id=task_id,
        collection_id=collection_id,
        creator_id=creator_id,
        status=ExportStatus.PENDING,
    )

    flask_mongo.db.export_tasks.insert_one(export_task.dict())

    thread = threading.Thread(target=_generate_export_in_background, args=(task_id, collection_id))
    thread.daemon = True
    thread.start()

    return jsonify(
        {"status": "success", "task_id": task_id, "status_url": f"/exports/{task_id}/status"}
    ), 202


@EXPORT.route("/exports/<string:task_id>/status", methods=["GET"])
def get_export_status(task_id: str):
    """Get the status of an export task.

    Parameters:
        task_id: The export task ID

    Returns:
        JSON response with task status and download URL if ready
    """

    task = flask_mongo.db.export_tasks.find_one({"task_id": task_id})

    if not task:
        return jsonify({"status": "error", "message": "Export task not found"}), 404

    response = {
        "status": task["status"],
        "created_at": task["created_at"].isoformat() if task.get("created_at") else None,
    }

    if task["status"] == ExportStatus.READY:
        response["download_url"] = f"/exports/{task_id}/download"
        response["completed_at"] = (
            task["completed_at"].isoformat() if task.get("completed_at") else None
        )

    if task["status"] == ExportStatus.ERROR:
        response["error_message"] = task.get("error_message")
        response["completed_at"] = (
            task["completed_at"].isoformat() if task.get("completed_at") else None
        )

    return jsonify(response), 200


@EXPORT.route("/exports/<string:task_id>/download", methods=["GET"])
def download_export(task_id: str):
    """Download the generated .eln file.

    Parameters:
        task_id: The export task ID

    Returns:
        The .eln file as attachment
    """

    task = flask_mongo.db.export_tasks.find_one({"task_id": task_id})

    if not task:
        return jsonify({"status": "error", "message": "Export task not found"}), 404

    if task["status"] != ExportStatus.READY:
        return jsonify(
            {"status": "error", "message": f"Export is not ready. Current status: {task['status']}"}
        ), 400

    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Export file not found"}), 404

    filename = f"{task['collection_id']}.eln"

    return send_file(
        file_path, as_attachment=True, download_name=filename, mimetype="application/vnd.eln+zip"
    )
