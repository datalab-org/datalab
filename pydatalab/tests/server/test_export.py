import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId

from pydatalab.models.tasks import ExportTaskSpec, Task, TaskStatus, TaskType


@pytest.fixture
def sample_collection(database, user_id):
    collection_data = {
        "_id": ObjectId(),
        "collection_id": "test_export_collection",
        "title": "Test Export Collection",
        "description": "Collection for testing export functionality",
        "creator_ids": [user_id],
    }

    database.collections.insert_one(collection_data)

    yield collection_data

    database.collections.delete_one({"collection_id": collection_data["collection_id"]})


@pytest.fixture
def mock_scheduler():
    with patch("pydatalab.routes.v0_1.export.export_scheduler") as mock_sched:
        mock_sched.add_job = MagicMock(return_value=None)
        yield mock_sched


def test_start_collection_export_success(client, sample_collection, mock_scheduler, database):
    collection_id = sample_collection["collection_id"]

    response = client.post(f"/collections/{collection_id}/export")

    assert response.status_code == 202

    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "task_id" in data
    assert "status_url" in data
    assert data["status_url"] == f"/exports/{data['task_id']}/status"

    assert mock_scheduler.add_job.called

    task = database.tasks.find_one({"task_id": data["task_id"]})
    assert task is not None
    assert task["spec"]["collection_id"] == collection_id
    assert task["status"] == TaskStatus.PENDING

    database.tasks.delete_one({"task_id": data["task_id"]})


def test_start_collection_export_not_found(client):
    response = client.post("/collections/nonexistent/export")
    assert response.status_code == 404

    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "not found" in data["message"].lower()


def test_get_export_status_pending(client, user_id, database):
    task_id = "test-task-pending"
    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/status")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "pending"
    assert "created_at" in data

    database.tasks.delete_one({"task_id": task_id})


def test_get_export_status_ready(client, user_id, database, tmp_path):
    task_id = "test-task-ready"
    file_path = tmp_path / f"{task_id}.eln"
    file_path.write_text("test content")

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.READY,
        completed_at=datetime.now(tz=timezone.utc),
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
            file_path=str(file_path),
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/status")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "ready"
    assert data["download_url"] == f"/exports/{task_id}/download"
    assert "completed_at" in data

    database.tasks.delete_one({"task_id": task_id})


def test_get_export_status_error(client, user_id, database):
    task_id = "test-task-error"
    error_message = "Export failed due to test error"

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.ERROR,
        error_message=error_message,
        completed_at=datetime.now(tz=timezone.utc),
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/status")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "error"
    assert data["error_message"] == error_message
    assert "completed_at" in data

    database.tasks.delete_one({"task_id": task_id})


def test_get_export_status_not_found(client):
    response = client.get("/exports/nonexistent-task/status")
    assert response.status_code == 404

    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "not found" in data["message"].lower()


def test_download_export_success(client, user_id, database, tmp_path):
    task_id = "test-download-task"
    collection_id = "test_collection"
    file_path = tmp_path / f"{task_id}.eln"
    file_path.write_bytes(b"test export content")

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.READY,
        spec=ExportTaskSpec(
            collection_id=collection_id,
            export_type="collection",
            file_path=str(file_path),
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/download")
    assert response.status_code == 200
    assert response.data == b"test export content"
    assert f"filename={collection_id}.eln" in response.headers.get("Content-Disposition", "")

    database.tasks.delete_one({"task_id": task_id})


def test_not_users_export_download(client, user_id, another_client, database):
    task_id = "not-this-users-task"

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PROCESSING,
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    response = another_client.get(f"/exports/{task_id}/download")
    assert response.status_code == 404
    database.tasks.delete_one({"task_id": task_id})


def test_download_export_not_ready(client, user_id, database):
    task_id = "test-not-ready-task"

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PROCESSING,
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/download")
    assert response.status_code == 400

    data = json.loads(response.data)
    assert "not ready" in data["message"].lower()

    database.tasks.delete_one({"task_id": task_id})


def test_download_export_file_missing(client, user_id, database):
    task_id = "test-missing-file-task"

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.READY,
        spec=ExportTaskSpec(
            collection_id="test_collection",
            export_type="collection",
            file_path="/nonexistent/path.eln",
        ),
    )
    database.tasks.insert_one(task.dict())

    response = client.get(f"/exports/{task_id}/download")
    assert response.status_code == 404

    data = json.loads(response.data)
    assert "file not found" in data["message"].lower()

    database.tasks.delete_one({"task_id": task_id})


def test_do_export_success(database, sample_collection, insert_default_sample, user_id):
    from pydatalab.routes.v0_1.export import _do_export

    task_id = "direct-collection-export-test"
    collection_id = sample_collection["collection_id"]

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            collection_id=collection_id,
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    _do_export(task_id, collection_id=collection_id, export_type="collection")

    updated_task = database.tasks.find_one({"task_id": task_id})
    assert updated_task["status"] == TaskStatus.READY
    assert os.path.exists(updated_task["spec"]["file_path"])

    os.remove(updated_task["spec"]["file_path"])
    database.tasks.delete_one({"task_id": task_id})

    task_id = "direct-item-export-test"
    item_id = insert_default_sample.item_id

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            item_id=item_id,
            export_type="item",
        ),
    )
    database.tasks.insert_one(task.dict())

    _do_export(task_id, item_id=item_id, export_type="item")

    updated_task = database.tasks.find_one({"task_id": task_id})
    assert updated_task["status"] == TaskStatus.READY
    assert os.path.exists(updated_task["spec"]["file_path"])

    os.remove(updated_task["spec"]["file_path"])
    database.tasks.delete_one({"task_id": task_id})


def test_do_export_error_handling(database, user_id):
    from pydatalab.routes.v0_1.export import _do_export

    task_id = "error-export-test"

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            collection_id="nonexistent_collection",
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    _do_export(task_id, collection_id="nonexistent_collection", export_type="collection")

    updated_task = database.tasks.find_one({"task_id": task_id})
    assert updated_task["status"] == TaskStatus.ERROR
    assert "error_message" in updated_task
    assert updated_task["completed_at"] is not None

    database.tasks.delete_one({"task_id": task_id})


def test_do_export_status_transitions(database, sample_collection, user_id):
    from pydatalab.routes.v0_1.export import _do_export

    task_id = "processing-status-test"
    collection_id = sample_collection["collection_id"]

    task = Task(
        type=TaskType.EXPORT,
        task_id=task_id,
        creator_id=user_id,
        status=TaskStatus.PENDING,
        spec=ExportTaskSpec(
            collection_id=collection_id,
            export_type="collection",
        ),
    )
    database.tasks.insert_one(task.dict())

    status_during_export = []

    def mock_create_eln(output_path, **kwargs):
        current_task = database.tasks.find_one({"task_id": task_id})
        status_during_export.append(current_task["status"])
        Path(output_path).write_text("test")

    with patch("pydatalab.routes.v0_1.export.create_eln_file", side_effect=mock_create_eln):
        _do_export(task_id, collection_id=collection_id, export_type="collection")

    assert TaskStatus.PROCESSING in status_during_export

    final_task = database.tasks.find_one({"task_id": task_id})
    assert final_task["status"] == TaskStatus.READY

    if final_task.get("spec", {}).get("file_path") and os.path.exists(
        final_task["spec"]["file_path"]
    ):
        os.remove(final_task["spec"]["file_path"])
    database.tasks.delete_one({"task_id": task_id})


def test_start_item_export_with_related_items(
    client, insert_default_sample, mock_scheduler, database, user_id
):
    item_id = insert_default_sample.item_id

    related_item = {
        "item_id": "related_item_for_export",
        "type": "samples",
        "creator_ids": [user_id],
        "relationships": [],
    }
    database.items.insert_one(related_item)

    request_data = {
        "include_related": True,
        "related_item_ids": [related_item["item_id"]],
    }

    response = client.post(f"/items/{item_id}/export", json=request_data)

    assert response.status_code == 202

    data = json.loads(response.data)
    task = database.tasks.find_one({"task_id": data["task_id"]})
    assert task["spec"]["export_type"] == "graph"
    assert mock_scheduler.add_job.called

    database.tasks.delete_one({"task_id": data["task_id"]})
    database.items.delete_one({"item_id": related_item["item_id"]})
