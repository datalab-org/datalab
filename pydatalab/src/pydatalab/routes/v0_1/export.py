import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, make_response, request, send_file
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.export import create_eln_file
from pydatalab.models.tasks import ExportTaskSpec, Task, TaskStage, TaskStatus, TaskType
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import PUBLIC_USER_ID, active_users_or_get_only
from pydatalab.scheduler import task_scheduler

EXPORT = Blueprint("export", __name__)

_app = None


@EXPORT.record_once
def _register_app(state):
    global _app
    _app = state.app


@EXPORT.before_request
@active_users_or_get_only
def _(): ...


def _do_export(
    task_id: str,
    collection_id: str | None = None,
    item_id: str | None = None,
    export_type: str = "collection",
    related_item_ids: list[str] | None = None,
):
    def add_stage(message: str, level: str = "info"):
        stage = TaskStage(timestamp=datetime.now(tz=timezone.utc), message=message, level=level)
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id}, {"$push": {"spec.stages": stage.dict()}}
        )

    try:
        flask_mongo.db.tasks.update_one(
            {"task_id": task_id}, {"$set": {"status": TaskStatus.PROCESSING}}
        )

        export_dir = Path(tempfile.gettempdir()) / "eln-exports"
        export_dir.mkdir(exist_ok=True, parents=True)

        output_path = export_dir / f"{task_id}.eln"

        if export_type == "collection":
            create_eln_file(str(output_path), collection_id=collection_id, on_stage=add_stage)
        elif export_type in ["item", "graph"]:
            create_eln_file(
                str(output_path),
                item_id=item_id,
                related_item_ids=related_item_ids,
                on_stage=add_stage,
            )

        flask_mongo.db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.READY,
                    "spec.file_path": str(output_path),
                    "completed_at": datetime.now(tz=timezone.utc),
                }
            },
        )

    except Exception as e:
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


def _generate_export_in_background(
    task_id: str,
    collection_id: str | None = None,
    item_id: str | None = None,
    export_type: str = "collection",
    related_item_ids: list[str] | None = None,
):
    import contextlib

    app_ctx = _app.app_context() if _app is not None else contextlib.nullcontext()
    with app_ctx:
        _do_export(task_id, collection_id, item_id, export_type, related_item_ids)


@EXPORT.route("/collections/<string:collection_id>/export", methods=["POST"])
def start_collection_export(collection_id: str):
    from pydatalab.permissions import get_default_permissions

    collection_with_perms = flask_mongo.db.collections.find_one(
        {"collection_id": collection_id, **get_default_permissions(user_only=False)}
    )
    if not collection_with_perms:
        return jsonify({"status": "error", "message": "Collection not found"}), 404

    task_id = str(uuid.uuid4())

    if not CONFIG.TESTING:
        creator_id = current_user.person.immutable_id
    else:
        creator_id = PUBLIC_USER_ID

    export_task = Task(
        task_id=task_id,
        type=TaskType.EXPORT,
        creator_id=creator_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            collection_id=collection_id,
            export_type="collection",
        ),
    )

    flask_mongo.db.tasks.insert_one(export_task.dict(exclude_none=False))

    task_scheduler.add_job(
        func=_generate_export_in_background,
        args=[task_id, collection_id, None, "collection", None],
        job_id=f"export_{task_id}",
    )

    return jsonify(
        {"status": "success", "task_id": task_id, "status_url": f"/exports/{task_id}/status"}
    ), 202


@EXPORT.route("/exports/<string:task_id>/status", methods=["GET"])
def get_export_status(task_id: str):
    task = flask_mongo.db.tasks.find_one(
        {
            "task_id": task_id,
            "creator_id": current_user.person.immutable_id,
            "type": TaskType.EXPORT,
        }
    )

    if not task:
        return jsonify({"status": "error", "message": "Export task not found"}), 404

    response = {
        "status": task["status"],
        "created_at": task["created_at"].isoformat() if task.get("created_at") else None,
    }

    if task.get("spec", {}).get("stages"):
        response["stages"] = task["spec"]["stages"]

    if task["status"] == TaskStatus.READY:
        response["download_url"] = f"/exports/{task_id}/download"
        response["completed_at"] = (
            task["completed_at"].isoformat() if task.get("completed_at") else None
        )

    if task["status"] == TaskStatus.ERROR:
        response["error_message"] = task.get("error_message")
        response["completed_at"] = (
            task["completed_at"].isoformat() if task.get("completed_at") else None
        )

    return jsonify(response), 200


# Internal nginx location that aliases the on-disk export directory (see
# `_do_export`, which writes to `<tempdir>/eln-exports/`). The matching nginx
# config marks this location `internal;` so clients cannot request it directly:
#
#     location /_protected_exports/ {
#         internal;
#         alias /tmp/eln-exports/;   # must match the export dir used in _do_export
#     }
#
# Only the basename of the export file is appended, so the alias above is the
# single source of truth for where the bytes live on disk.
X_ACCEL_EXPORT_LOCATION = "/_protected_exports"

EXPORT_MIMETYPE = "application/vnd.eln+zip"


def _serve_export_file(file_path: str, filename: str):
    """Return a response that delivers a generated export file to the client.

    When `CONFIG.USE_X_ACCEL_REDIRECT` is enabled (nginx deployments), the
    gunicorn worker does *not* stream the bytes itself: it returns an empty
    response carrying an `X-Accel-Redirect` header, and nginx serves the file
    off disk with kernel sendfile. This frees the worker the instant auth
    passes, so multi-GB downloads no longer tie up (or time out) a worker.

    Otherwise (dev/test, a non-nginx proxy, or running without a proxy) we fall
    back to streaming the file directly through Flask with `send_file`.
    """
    if CONFIG.USE_X_ACCEL_REDIRECT:
        # Map the absolute on-disk path to the internal nginx location by
        # basename; nginx's `alias` resolves it back to the real directory.
        internal_uri = f"{X_ACCEL_EXPORT_LOCATION}/{Path(file_path).name}"

        response = make_response("")
        response.headers["X-Accel-Redirect"] = internal_uri
        response.headers["Content-Type"] = EXPORT_MIMETYPE
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        # Deliberately omit Content-Length: nginx sets it from the file it serves.
        return response

    return send_file(
        file_path, as_attachment=True, download_name=filename, mimetype=EXPORT_MIMETYPE
    )


@EXPORT.route("/exports/<string:task_id>/download", methods=["GET"])
def download_export(task_id: str):
    if not CONFIG.TESTING:
        current_creator_id = current_user.person.immutable_id
        task = flask_mongo.db.tasks.find_one(
            {"task_id": task_id, "creator_id": current_creator_id, "type": TaskType.EXPORT}
        )
    else:
        task = flask_mongo.db.tasks.find_one({"task_id": task_id, "type": TaskType.EXPORT})

    if not task:
        return jsonify({"status": "error", "message": "Export task not found"}), 404

    if task["status"] != TaskStatus.READY:
        return jsonify(
            {"status": "error", "message": f"Export is not ready. Current status: {task['status']}"}
        ), 400

    spec = task.get("spec", {})
    file_path = spec.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Export file not found"}), 404

    filename = f"{spec.get('collection_id') or spec.get('item_id')}.eln"

    return _serve_export_file(file_path, filename)


@EXPORT.route("/items/<string:item_id>/export", methods=["POST"])
def start_item_export(item_id: str):
    from pydatalab.permissions import get_default_permissions

    item_data = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=False)}
    )
    if not item_data:
        return jsonify({"status": "error", "message": "Item not found"}), 404

    task_id = str(uuid.uuid4())

    if not CONFIG.TESTING:
        creator_id = current_user.person.immutable_id
    else:
        creator_id = PUBLIC_USER_ID

    export_type = "item"
    related_item_ids = None

    request_data = request.get_json() or {}
    if request_data.get("include_related"):
        related_item_ids = request_data.get("related_item_ids", [])
        if not related_item_ids:
            return jsonify(
                {
                    "status": "error",
                    "message": "related_item_ids required when include_related is true",
                }
            ), 400
        export_type = "graph"

    export_task = Task(
        task_id=task_id,
        type=TaskType.EXPORT,
        creator_id=creator_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            item_id=item_id,
            export_type=export_type,
        ),
    )

    flask_mongo.db.tasks.insert_one(export_task.dict(exclude_none=False))

    task_scheduler.add_job(
        func=_generate_export_in_background,
        args=[task_id, None, item_id, export_type, related_item_ids],
        job_id=f"export_{task_id}",
    )

    return jsonify(
        {"status": "success", "task_id": task_id, "status_url": f"/exports/{task_id}/status"}
    ), 202
