"""Tests for asynchronous block processing.

Tests the full async pipeline: task creation, status polling, GridFS
transfer buffer, stage tracking, cleanup, and config-driven opt-in.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import gridfs
import pytest

from pydatalab.models.tasks import BlockProcessingTaskSpec, Task, TaskStage, TaskStatus, TaskType


@pytest.fixture(autouse=True)
def _set_app(app):
    """Ensure the module-level _app reference is set for background tasks."""
    import pydatalab.routes.v0_1.blocks as blocks_mod

    blocks_mod._app = app
    yield
    blocks_mod._app = None


@pytest.fixture
def mock_scheduler():
    with patch("pydatalab.routes.v0_1.blocks.task_scheduler") as mock_sched:
        mock_sched.add_job = MagicMock(return_value=None)
        yield mock_sched


@pytest.fixture
def sample_with_block(admin_client, default_sample_dict, database):
    """Creates a sample with a comment block and returns (item_id, block_id, block_data)."""
    import uuid

    sample_id = f"test_async_sample_{uuid.uuid4().hex[:8]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201

    response = admin_client.post(
        "/add-data-block/",
        json={"block_type": "comment", "item_id": sample_id, "index": 0},
    )
    assert response.status_code == 200
    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]

    # Re-fetch to get the full block data as stored
    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    block_data = response.json["item_data"]["blocks_obj"][block_id]

    yield sample_id, block_id, block_data

    database.items.delete_one({"item_id": sample_id})


class TestAsyncUpdateBlock:
    """Tests for the update_block route when async processing is triggered."""

    def test_update_block_returns_202_when_async(
        self, admin_client, sample_with_block, mock_scheduler, database
    ):
        """When a block type is in ASYNC_BLOCK_TYPES, update_block should return
        202 with a task_id and schedule a job."""
        item_id, block_id, block_data = sample_with_block

        with patch("pydatalab.config.CONFIG.ASYNC_BLOCK_TYPES", ["comment"]):
            response = admin_client.post("/update-block/", json={"block_data": block_data})

        assert response.status_code == 202
        data = response.json
        assert data["status"] == "success"
        assert data["processing_async"] is True
        assert "task_id" in data
        assert data["status_url"] == f"/blocks/{data['task_id']}/status"

        # Verify task was created in the database
        task = database.tasks.find_one({"task_id": data["task_id"]})
        assert task is not None
        assert task["status"] == TaskStatus.PENDING
        assert task["type"] == TaskType.BLOCK_PROCESSING
        assert task["spec"]["item_id"] == item_id
        assert task["spec"]["block_id"] == block_id
        assert len(task["spec"]["stages"]) == 1

        # Verify scheduler was called
        assert mock_scheduler.add_job.called

        database.tasks.delete_one({"task_id": data["task_id"]})

    def test_update_block_returns_200_when_not_async(self, admin_client, sample_with_block):
        """When a block type is NOT in ASYNC_BLOCK_TYPES, update_block should
        process synchronously and return 200."""
        _, _, block_data = sample_with_block

        response = admin_client.post("/update-block/", json={"block_data": block_data})

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "new_block_data" in response.json

    def test_prefers_async_class_attr_triggers_async(
        self, admin_client, sample_with_block, mock_scheduler, database
    ):
        """Blocks with _prefers_async=True should be processed async even when
        not listed in ASYNC_BLOCK_TYPES."""
        _, _, block_data = sample_with_block

        FakeBlock = type(
            "FakeBlock",
            (),
            {
                "_prefers_async": True,
                "from_web": classmethod(lambda cls, x: MagicMock()),
            },
        )
        with patch.dict(
            "pydatalab.routes.v0_1.blocks.BLOCK_TYPES",
            {"comment": FakeBlock},
        ):
            response = admin_client.post("/update-block/", json={"block_data": block_data})

        assert response.status_code == 202
        task_id = response.json["task_id"]
        database.tasks.delete_one({"task_id": task_id})


class TestBlockTaskStatus:
    """Tests for the /blocks/<task_id>/status endpoint."""

    def test_status_pending(self, client, user_id, database):
        task_id = "test-block-pending"
        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PENDING,
            spec=BlockProcessingTaskSpec(
                item_id="test_item",
                block_id="test_block",
            ),
        )
        database.tasks.insert_one(task.model_dump())

        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "pending"
        assert data["task_id"] == task_id
        assert "created_at" in data

        database.tasks.delete_one({"task_id": task_id})

    def test_status_processing_with_stages(self, client, user_id, database):
        task_id = "test-block-processing"
        stages = [
            TaskStage(
                timestamp=datetime.now(tz=timezone.utc),
                message="Processing started",
            ),
            TaskStage(
                timestamp=datetime.now(tz=timezone.utc),
                message="Loading comment block from database",
            ),
        ]
        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PROCESSING,
            spec=BlockProcessingTaskSpec(
                item_id="test_item",
                block_id="test_block",
                stages=stages,
            ),
        )
        database.tasks.insert_one(task.model_dump())

        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "processing"
        assert len(data["stages"]) == 2
        assert data["stages"][0]["message"] == "Processing started"
        assert data["stages"][1]["message"] == "Loading comment block from database"
        # Verify timestamps are serialized as strings
        for stage in data["stages"]:
            assert isinstance(stage["timestamp"], str)

        database.tasks.delete_one({"task_id": task_id})

    def test_status_ready_with_gridfs_data(self, client, user_id, database, app):
        """When a task is READY and GridFS data exists, the status endpoint should
        return the block data and clean up the GridFS file."""
        task_id = "test-block-ready-gridfs"
        item_id = "test_item_ready"
        block_id = "test_block_ready"

        # Create an item with the block so the permission check passes
        database.items.insert_one(
            {
                "item_id": item_id,
                "type": "samples",
                "creator_ids": [user_id],
                "blocks_obj": {block_id: {"blocktype": "comment", "block_id": block_id}},
            }
        )

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.READY,
            completed_at=datetime.now(tz=timezone.utc),
            spec=BlockProcessingTaskSpec(
                item_id=item_id,
                block_id=block_id,
            ),
        )
        database.tasks.insert_one(task.model_dump())

        # Write block data to GridFS
        from pydatalab.mongo import get_database

        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        block_data = {"blocktype": "comment", "block_id": block_id, "test_key": "test_value"}
        bucket.upload_from_stream(task_id, json.dumps(block_data).encode("utf-8"))

        # Poll status — should return block data
        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "ready"
        assert data["block_data"] is not None
        assert data["block_data"]["test_key"] == "test_value"

        # GridFS file should have been deleted on delivery
        assert list(bucket.find({"filename": task_id})) == []

        database.tasks.delete_one({"task_id": task_id})
        database.items.delete_one({"item_id": item_id})

    def test_status_ready_no_gridfs_data(self, client, user_id, database):
        """When a task is READY but the GridFS file is missing, block_data should be None."""
        task_id = "test-block-ready-no-gridfs"
        item_id = "test_item_no_gridfs"
        block_id = "test_block_no_gridfs"

        database.items.insert_one(
            {
                "item_id": item_id,
                "type": "samples",
                "creator_ids": [user_id],
                "blocks_obj": {block_id: {"blocktype": "comment", "block_id": block_id}},
            }
        )

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.READY,
            completed_at=datetime.now(tz=timezone.utc),
            spec=BlockProcessingTaskSpec(
                item_id=item_id,
                block_id=block_id,
            ),
        )
        database.tasks.insert_one(task.model_dump())

        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "ready"
        assert data["block_data"] is None

        database.tasks.delete_one({"task_id": task_id})
        database.items.delete_one({"item_id": item_id})

    def test_status_error(self, client, user_id, database):
        task_id = "test-block-error"
        error_message = "Block processing failed"

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.ERROR,
            error_message=error_message,
            completed_at=datetime.now(tz=timezone.utc),
            spec=BlockProcessingTaskSpec(
                item_id="test_item",
                block_id="test_block",
            ),
        )
        database.tasks.insert_one(task.model_dump())

        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error_message"] == error_message

        database.tasks.delete_one({"task_id": task_id})

    def test_status_not_found(self, client):
        response = client.get("/blocks/nonexistent-task-id/status")
        assert response.status_code == 404

    def test_status_ignores_export_tasks(self, client, user_id, database):
        """The block status endpoint should not return export tasks."""
        from pydatalab.models.tasks import ExportTaskSpec

        task_id = "test-export-not-block"
        task = Task(
            task_id=task_id,
            type=TaskType.EXPORT,
            creator_id=user_id,
            status=TaskStatus.READY,
            spec=ExportTaskSpec(
                collection_id="test",
                export_type="collection",
            ),
        )
        database.tasks.insert_one(task.model_dump())

        response = client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 404

        database.tasks.delete_one({"task_id": task_id})

    def test_status_ready_respects_permissions(self, another_client, user_id, database):
        """When the polling user doesn't have permission to the item, block_data
        should not be returned even if the task is READY."""
        task_id = "test-block-ready-no-perms"
        item_id = "test_item_perms"
        block_id = "test_block_perms"

        # Item is owned by user_id, but we poll with another_client
        database.items.insert_one(
            {
                "item_id": item_id,
                "type": "samples",
                "creator_ids": [user_id],
                "blocks_obj": {block_id: {"blocktype": "comment", "block_id": block_id}},
            }
        )

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.READY,
            completed_at=datetime.now(tz=timezone.utc),
            spec=BlockProcessingTaskSpec(
                item_id=item_id,
                block_id=block_id,
            ),
        )
        database.tasks.insert_one(task.model_dump())

        from pydatalab.mongo import get_database

        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        bucket.upload_from_stream(task_id, json.dumps({"test": "data"}).encode("utf-8"))

        response = another_client.get(f"/blocks/{task_id}/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ready"
        # block_data should not be present since the item permission check fails
        assert "block_data" not in data

        # GridFS file should still exist (not consumed by another user)
        assert len(list(bucket.find({"filename": task_id}))) == 1

        # Clean up GridFS
        for f in bucket.find({"filename": task_id}):
            bucket.delete(f._id)
        database.tasks.delete_one({"task_id": task_id})
        database.items.delete_one({"item_id": item_id})


class TestProcessBlockAsync:
    """Tests for the _process_block_async function directly."""

    def test_successful_processing(self, app, user_id, database):
        """Test that _process_block_async transitions through PROCESSING -> READY,
        writes stages, and uploads to GridFS."""
        from pydatalab.routes.v0_1.blocks import _process_block_async

        task_id = "test-direct-async"
        item_id = "test_item_direct"
        block_id = "test_block_direct"

        # Insert sample and block
        database.items.insert_one(
            {
                "item_id": item_id,
                "type": "samples",
                "creator_ids": [user_id],
                "blocks_obj": {
                    block_id: {
                        "blocktype": "comment",
                        "block_id": block_id,
                        "item_id": item_id,
                    },
                },
            }
        )

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PENDING,
            spec=BlockProcessingTaskSpec(item_id=item_id, block_id=block_id),
        )
        database.tasks.insert_one(task.model_dump())

        block_data = {
            "blocktype": "comment",
            "block_id": block_id,
            "item_id": item_id,
        }

        _process_block_async(task_id, block_data, None, str(user_id))

        # Check final task state
        updated_task = database.tasks.find_one({"task_id": task_id})
        assert updated_task["status"] == TaskStatus.READY
        assert updated_task["completed_at"] is not None
        assert len(updated_task["spec"]["stages"]) >= 4

        # Check GridFS data was written
        from pydatalab.mongo import get_database

        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        stream = bucket.open_download_stream_by_name(task_id)
        gridfs_data = json.loads(stream.read())
        assert gridfs_data["blocktype"] == "comment"

        # Clean up
        bucket.delete(stream._id)
        database.tasks.delete_one({"task_id": task_id})
        database.items.delete_one({"item_id": item_id})

    def test_processing_error_handling(self, app, user_id, database):
        """Test that errors during processing are caught and the task is marked ERROR."""
        from pydatalab.routes.v0_1.blocks import _process_block_async

        task_id = "test-direct-async-error"

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PENDING,
            spec=BlockProcessingTaskSpec(item_id="x", block_id="y"),
        )
        database.tasks.insert_one(task.model_dump())

        # Pass an invalid block type to trigger an error
        block_data = {
            "blocktype": "nonexistent_type",
            "block_id": "y",
            "item_id": "x",
        }

        _process_block_async(task_id, block_data, None, str(user_id))

        updated_task = database.tasks.find_one({"task_id": task_id})
        assert updated_task["status"] == TaskStatus.ERROR
        assert updated_task["error_message"] is not None
        assert updated_task["completed_at"] is not None

        # Check that error stage was recorded
        error_stages = [s for s in updated_task["spec"]["stages"] if s["level"] == "error"]
        assert len(error_stages) >= 1

        database.tasks.delete_one({"task_id": task_id})


class TestCleanupStaleTasks:
    """Tests for _cleanup_stale_tasks."""

    def test_marks_timed_out_tasks_as_error(self, app, user_id, database):
        from pydatalab.routes.v0_1.blocks import _cleanup_stale_tasks

        task_id = "test-timeout-cleanup"
        old_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PROCESSING,
            spec=BlockProcessingTaskSpec(item_id="x", block_id="y"),
        )
        task_dict = task.model_dump()
        task_dict["created_at"] = old_time
        database.tasks.insert_one(task_dict)

        _cleanup_stale_tasks()

        updated = database.tasks.find_one({"task_id": task_id})
        assert updated["status"] == TaskStatus.ERROR
        assert "timed out" in updated["error_message"].lower()
        assert updated["completed_at"] is not None

        database.tasks.delete_one({"task_id": task_id})

    def test_does_not_timeout_recent_tasks(self, app, user_id, database):
        from pydatalab.routes.v0_1.blocks import _cleanup_stale_tasks

        task_id = "test-no-timeout"

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.PROCESSING,
            spec=BlockProcessingTaskSpec(item_id="x", block_id="y"),
        )
        database.tasks.insert_one(task.model_dump())

        _cleanup_stale_tasks()

        updated = database.tasks.find_one({"task_id": task_id})
        assert updated["status"] == TaskStatus.PROCESSING

        database.tasks.delete_one({"task_id": task_id})

    def test_purges_old_completed_tasks_and_gridfs(self, app, user_id, database):
        from pydatalab.mongo import get_database
        from pydatalab.routes.v0_1.blocks import _cleanup_stale_tasks

        task_id = "test-purge-old"
        old_time = datetime.now(tz=timezone.utc) - timedelta(hours=8)

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.READY,
            completed_at=old_time,
            spec=BlockProcessingTaskSpec(item_id="x", block_id="y"),
        )
        task_dict = task.model_dump()
        task_dict["created_at"] = old_time
        database.tasks.insert_one(task_dict)

        # Add orphaned GridFS file
        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        bucket.upload_from_stream(task_id, b'{"test": true}')

        _cleanup_stale_tasks()

        # Task should be deleted
        assert database.tasks.find_one({"task_id": task_id}) is None
        # GridFS file should be deleted
        assert list(bucket.find({"filename": task_id})) == []

    def test_does_not_purge_recent_completed_tasks(self, app, user_id, database):
        from pydatalab.routes.v0_1.blocks import _cleanup_stale_tasks

        task_id = "test-no-purge"

        task = Task(
            task_id=task_id,
            type=TaskType.BLOCK_PROCESSING,
            creator_id=user_id,
            status=TaskStatus.READY,
            completed_at=datetime.now(tz=timezone.utc),
            spec=BlockProcessingTaskSpec(item_id="x", block_id="y"),
        )
        database.tasks.insert_one(task.model_dump())

        _cleanup_stale_tasks()

        assert database.tasks.find_one({"task_id": task_id}) is not None

        database.tasks.delete_one({"task_id": task_id})


class TestEndToEndAsyncBlock:
    """Integration tests that exercise the full async pipeline via HTTP:
    submit → poll status → collect results, with no mocked scheduler."""

    def test_async_block_full_lifecycle(self, admin_client, sample_with_block, database):
        """Submit an update-block request that triggers async processing,
        then poll the status URL until READY and verify the block data
        is returned."""
        import time

        item_id, block_id, block_data = sample_with_block

        with patch("pydatalab.config.CONFIG.ASYNC_BLOCK_TYPES", ["comment"]):
            response = admin_client.post("/update-block/", json={"block_data": block_data})

        assert response.status_code == 202
        data = response.json
        assert data["processing_async"] is True
        task_id = data["task_id"]
        status_url = data["status_url"]

        # Poll the status endpoint until the task completes or we time out
        deadline = time.monotonic() + 10
        final_response = None
        while time.monotonic() < deadline:
            status_response = admin_client.get(status_url)
            assert status_response.status_code == 200
            status_data = status_response.json
            assert status_data["task_id"] == task_id

            if status_data["status"] in (TaskStatus.READY, TaskStatus.ERROR):
                final_response = status_data
                break
            time.sleep(0.2)

        assert final_response is not None, (
            f"Task did not complete within 10s, last status: {status_data}"
        )
        assert final_response["status"] == TaskStatus.READY
        assert final_response["completed_at"] is not None

        # Block data should have been returned from the GridFS transfer buffer
        assert "block_data" in final_response
        assert final_response["block_data"] is not None
        assert final_response["block_data"]["blocktype"] == "comment"

        # Processing stages should be present
        assert "stages" in final_response
        assert len(final_response["stages"]) >= 4

        # GridFS data should have been cleaned up on delivery
        from pydatalab.mongo import get_database

        bucket = gridfs.GridFSBucket(get_database(), bucket_name="block_data")
        assert list(bucket.find({"filename": task_id})) == []

        database.tasks.delete_one({"task_id": task_id})
