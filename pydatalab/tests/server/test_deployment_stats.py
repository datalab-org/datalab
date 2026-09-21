# This file was edited with the assistance of an AI model and requires human review from the contributor.
from datetime import datetime, timedelta
from datetime import timezone as tz

from bson import ObjectId

from pydatalab.deployment_stats import (
    STATS_COLLECTION,
    clear_stats_cache,
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

    clear_stats_cache()
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
    clear_stats_cache()


def test_stats_history_requires_login(unauthenticated_client):
    response = unauthenticated_client.get("/info/stats/history")
    assert response.status_code == 401
