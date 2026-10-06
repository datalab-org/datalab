from datetime import datetime, timedelta
from datetime import timezone as tz
from unittest.mock import MagicMock, patch

from bson import ObjectId

from pydatalab.deployment_stats import (
    STATS_COLLECTION,
    update_deployment_stats,
)


def _oid(dt: datetime) -> ObjectId:
    """An ObjectId for the given creation time, with random trailing bytes so that it is unique."""
    return ObjectId(ObjectId.from_datetime(dt).binary[:4] + ObjectId().binary[4:])


def test_stats_history(client, database, user_id):
    historic = datetime(2020, 1, 15, tzinfo=tz.utc)
    database.items.insert_many(
        [
            {
                "_id": _oid(historic),
                "type": "samples",
                "item_id": "stats_sample_1",
                "refcode": "test:stats_sample_1",
                "creator_ids": [user_id],
                "blocks_obj": {"a": {"blocktype": "xrd"}, "b": {"blocktype": "comment"}},
            },
            {
                "_id": _oid(historic + timedelta(seconds=1)),
                "type": "samples",
                "item_id": "stats_sample_2",
                "refcode": "test:stats_sample_2",
                "creator_ids": [user_id],
            },
            {
                "_id": _oid(historic + timedelta(days=31)),
                "type": "cells",
                "item_id": "stats_cell_1",
                "refcode": "test:stats_cell_1",
                "creator_ids": [user_id],
                "blocks_obj": {"c": {"blocktype": "xrd"}},
            },
        ]
    )
    database.files.insert_one({"_id": _oid(historic), "size": 1024})
    update_deployment_stats(database)
    response = client.get("/info/stats/history")
    assert response.status_code == 200
    data = response.json["data"]

    # Every month from the first recorded one up to now is present
    assert data["months"][0] == "2020-01"
    assert data["months"][1] == "2020-02"
    assert data["months"][-1] == datetime.now(tz=tz.utc).strftime("%Y-%m")
    assert all(len(data[key]) == len(data["months"]) for key in ("users", "files", "file_bytes"))

    assert data["items"]["samples"][0] == 2
    assert data["items"]["cells"][0] == 0
    assert data["items"]["cells"][1] == 1
    assert data["active_users"][0] == 1
    assert data["files"][0] == 1
    assert data["file_bytes"][0] == 1024
    assert data["blocks"] == {"xrd": 2, "comment": 1}
    assert data["totals"]["items"]["samples"] >= 2
    assert data["totals"]["blocks"] == 3

    # The monthly histograms are persisted in their own collection
    assert database[STATS_COLLECTION].find_one({"_id": "2020-01"})["items"] == {"samples": 2}

    # An incremental update only touches the latest stored month onwards, so closed-off
    # months are kept as a historical record even if the underlying items are deleted
    this_month = datetime.now(tz=tz.utc).strftime("%Y-%m")
    database.items.delete_one({"item_id": "stats_sample_2"})
    database.items.insert_one(
        {
            "_id": ObjectId(),
            "type": "samples",
            "item_id": "stats_sample_3",
            "refcode": "test:stats_sample_3",
            "creator_ids": [],
        }
    )
    update_deployment_stats(database)
    assert database[STATS_COLLECTION].find_one({"_id": "2020-01"})["items"] == {"samples": 2}
    assert database[STATS_COLLECTION].find_one({"_id": this_month})["items"]["samples"] >= 1

    # A full rebuild reflects the current state of the database
    update_deployment_stats(database, full=True)
    assert database[STATS_COLLECTION].find_one({"_id": "2020-01"})["items"] == {"samples": 1}

    database.items.delete_many({"item_id": {"$regex": "^stats_"}})
    database.files.delete_many({"size": 1024})
    database[STATS_COLLECTION].delete_many({})


def test_stats_history_counts_referenced_blocks(client, database, user_id):
    block_id = ObjectId()
    database.blocks.insert_one({"_id": block_id, "block_id": "ref", "blocktype": "nmr"})
    database.items.insert_one(
        {
            "_id": ObjectId(),
            "type": "samples",
            "item_id": "stats_ref_sample",
            "refcode": "test:stats_ref_sample",
            "creator_ids": [user_id],
            "blocks_obj": {"ref": {"immutable_id": block_id}, "legacy": {"blocktype": "xrd"}},
        }
    )
    update_deployment_stats(database)
    response = client.get("/info/stats/history")
    assert response.status_code == 200
    data = response.json["data"]
    assert data["blocks"] == {"nmr": 1, "xrd": 1}
    assert data["totals"]["blocks"] == 2

    database.items.delete_many({"item_id": {"$regex": "^stats_"}})
    database.blocks.delete_one({"_id": block_id})
    database[STATS_COLLECTION].delete_many({})


def test_stats_history_requires_login(unauthenticated_client):
    response = unauthenticated_client.get("/info/stats/history")
    assert response.status_code == 401


def test_stale_stats_update_in_background(client, database):
    database[STATS_COLLECTION].delete_many({})
    with patch("pydatalab.routes.v0_1.info.task_scheduler") as mock_scheduler:
        mock_scheduler.add_job = MagicMock(return_value=None)
        response = client.get("/info/stats/history")
    assert response.status_code == 200
    assert response.json["data"]["updating"] is True
    assert response.json["data"]["months"] == []
    assert response.headers["Cache-Control"] == "no-store"
    assert mock_scheduler.add_job.called

    update_deployment_stats(database)
    response = client.get("/info/stats/history")
    assert response.json["data"]["updating"] is False
    assert response.json["data"]["months"]

    database[STATS_COLLECTION].delete_many({})
