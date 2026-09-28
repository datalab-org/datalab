"""Historical usage statistics for a deployment.

Monthly histograms of new entries (items, users, files, collections, ...) are
stored in their own database collection (`deployment_stats`), with one
document per calendar month. The collection is updated incrementally: only the
most recent stored month (which may have been partial when last computed) and
any subsequent months are recomputed, using the creation time embedded in each
document's `ObjectId`, so an update only scans documents created since then.

Months that have been closed off are therefore a historical record of what was
created in that month; later deletions do not rewrite history.

Each update also stores a snapshot of the current totals and block type counts on
the current month's document, so serving the stats is just a read of this
collection; the database itself acts as the cache, refreshed when the latest
update is older than `STATS_REFRESH_INTERVAL`.

"""

from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime, timedelta
from datetime import timezone as tz
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from pydatalab.logger import LOGGER

STATS_COLLECTION = "deployment_stats"
"""The name of the database collection that stores the monthly histograms."""

STATS_REFRESH_INTERVAL = timedelta(hours=24)
"""How long a computed set of histograms (and the served summary) is considered fresh."""

EARLIEST_DATE = datetime(2019, 1, 1, tzinfo=tz.utc)
"""Entries with ObjectIds that claim to be older than this, or to be from the future
(e.g., hand-crafted IDs such as `000000000000000000000000`), are excluded from the histograms."""

_MONTH_FORMAT = "%Y-%m"

_MONTH_OF_ID = {"$dateToString": {"format": _MONTH_FORMAT, "date": {"$toDate": "$_id"}}}
"""Aggregation expression for the creation month (`YYYY-MM`) of a document's `ObjectId`."""


def _months(start: datetime, end: datetime) -> Iterator[str]:
    """Yield the keys (`YYYY-MM`) of every month from `start` to `end` inclusive."""
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield f"{year:04d}-{month:02d}"
        year, month = year + month // 12, month % 12 + 1


def _group_by_month(**accumulators) -> dict:
    return {"$group": {"_id": {"month": _MONTH_OF_ID}, "count": {"$sum": 1}, **accumulators}}


def _empty_month() -> dict[str, Any]:
    return {
        "items": {},
        "users": 0,
        "active_users": 0,
        "files": 0,
        "file_bytes": 0,
        "collections": 0,
        "versions": 0,
    }


def _compute_monthly_histograms(db: Database, since: datetime | None) -> dict[str, dict]:
    """Aggregate the per-month counts of each tracked entity created at or after `since`.

    Returns:
        A dictionary keyed by month (`YYYY-MM`) containing the stats for that month.

    """
    months: dict[str, dict] = defaultdict(_empty_month)
    active_users: dict[str, set] = defaultdict(set)
    # Only count plausible ObjectIds, created between `since` (or `EARLIEST_DATE`) and now
    match = {
        "$match": {
            "_id": {
                "$type": "objectId",
                "$gte": ObjectId.from_datetime(max(since or EARLIEST_DATE, EARLIEST_DATE)),
                "$lt": ObjectId.from_datetime(datetime.now(tz=tz.utc) + timedelta(days=1)),
            }
        }
    }

    by_type = {"$group": {"_id": {"month": _MONTH_OF_ID, "type": "$type"}, "count": {"$sum": 1}}}
    for doc in db.items.aggregate([match, by_type]):
        item_type = doc["_id"].get("type") or "unknown"
        months[doc["_id"]["month"]]["items"][item_type] = doc["count"]

    # Anyone who created an item in a given month counts as active in that month
    for doc in db.items.aggregate(
        [
            match,
            {"$unwind": "$creator_ids"},
            _group_by_month(users={"$addToSet": "$creator_ids"}),
        ]
    ):
        active_users[doc["_id"]["month"]].update(str(u) for u in doc["users"] if u is not None)

    for doc in db.users.aggregate([match, _group_by_month()]):
        months[doc["_id"]["month"]]["users"] = doc["count"]

    for doc in db.collections.aggregate([match, _group_by_month()]):
        months[doc["_id"]["month"]]["collections"] = doc["count"]

    for doc in db.files.aggregate(
        [match, _group_by_month(bytes={"$sum": {"$ifNull": ["$size", 0]}})]
    ):
        months[doc["_id"]["month"]]["files"] = doc["count"]
        months[doc["_id"]["month"]]["file_bytes"] = doc["bytes"]

    # Item versions record saves (and their authors) and so capture activity on existing items
    for doc in db.item_versions.aggregate(
        [match, _group_by_month(users={"$addToSet": "$user_id"})]
    ):
        month = doc["_id"]["month"]
        months[month]["versions"] = doc["count"]
        active_users[month].update(str(u) for u in doc["users"] if u is not None)

    for month, users in active_users.items():
        months[month]["active_users"] = len(users)

    return dict(months)


def update_deployment_stats(db: Database, full: bool = False) -> int:
    """Incrementally update the monthly histograms stored in the `deployment_stats` collection.

    Parameters:
        db: The database to compute the stats for (and store them in).
        full: Whether to discard any stored histograms and recompute everything from scratch.

    Returns:
        The number of monthly documents written.

    """
    collection = db[STATS_COLLECTION]
    now = datetime.now(tz=tz.utc)

    since: datetime | None = None
    if full:
        collection.delete_many({})
    else:
        latest = collection.find_one(sort=[("_id", -1)])
        if latest:
            since = datetime.strptime(latest["_id"], _MONTH_FORMAT).replace(tzinfo=tz.utc)

    histograms = _compute_monthly_histograms(db, since)

    # Make sure every month from `since` to now has an entry, so that recomputed months
    # with no remaining activity are zeroed rather than left stale
    for month in _months(since or now, now):
        histograms.setdefault(month, _empty_month())

    # The current month also holds a snapshot of the current totals; `$set` leaves
    # the last snapshot on previous months in place, as a record of their end state
    blocks = _block_type_counts(db)
    totals = _current_totals(db)
    totals["blocks"] = sum(blocks.values())
    histograms[now.strftime(_MONTH_FORMAT)].update({"blocks": blocks, "totals": totals})

    for month, stats in histograms.items():
        collection.update_one(
            {"_id": month},
            {"$set": {**stats, "updated_at": now}},
            upsert=True,
        )

    LOGGER.info(
        "Updated %d monthly entries in %s (since %s)", len(histograms), STATS_COLLECTION, since
    )
    return len(histograms)


def _block_type_counts(db: Database) -> dict[str, int]:
    """Count the blocks of each type currently attached to items.

    Legacy blocks are embedded in `blocks_obj` with their `blocktype`; newer blocks
    are stored there as `{"immutable_id": ...}` references, whose type is looked up
    from the `blocks` collection.
    """
    pipeline = [
        {"$match": {"blocks_obj": {"$type": "object"}}},
        {"$project": {"blocks": {"$objectToArray": "$blocks_obj"}}},
        {"$unwind": "$blocks"},
        {
            "$lookup": {
                "from": "blocks",
                "let": {"ref": "$blocks.v.immutable_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$ref"]}}},
                    {"$project": {"_id": 0, "blocktype": 1}},
                ],
                "as": "referenced",
            }
        },
        {
            "$group": {
                "_id": {
                    "$ifNull": [
                        "$blocks.v.blocktype",
                        {"$arrayElemAt": ["$referenced.blocktype", 0]},
                    ]
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]
    return {str(doc["_id"]): doc["count"] for doc in db.items.aggregate(pipeline) if doc["_id"]}


def _current_totals(db: Database) -> dict[str, Any]:
    items_by_type = {
        str(doc["_id"]): doc["count"]
        for doc in db.items.aggregate([{"$group": {"_id": "$type", "count": {"$sum": 1}}}])
        if doc["_id"]
    }
    total_size = {"$group": {"_id": None, "bytes": {"$sum": {"$ifNull": ["$size", 0]}}}}
    file_bytes = next(db.files.aggregate([total_size]), {"bytes": 0})["bytes"]
    return {
        "items": items_by_type,
        "users": db.users.count_documents({}),
        "files": db.files.count_documents({}),
        "file_bytes": file_bytes,
        "collections": db.collections.count_documents({}),
    }


def build_stats_summary(db: Database) -> dict[str, Any]:
    """Build the columnar summary of the stored histograms served by the API.

    Every month between the first recorded month and the current one is present,
    so that each series can be plotted directly against `months`.

    """
    docs = {doc["_id"]: doc for doc in db[STATS_COLLECTION].find()}
    months: list[str] = []
    if docs:
        first = datetime.strptime(min(docs), _MONTH_FORMAT).replace(tzinfo=tz.utc)
        months = list(_months(first, datetime.now(tz=tz.utc)))

    item_types = sorted({t for doc in docs.values() for t in doc.get("items", {})})
    scalar_series = [key for key in _empty_month() if key != "items"]

    empty: dict[str, Any] = {}
    latest = docs[max(docs)] if docs else empty
    return {
        "months": months,
        "items": {
            item_type: [docs.get(m, empty).get("items", {}).get(item_type, 0) for m in months]
            for item_type in item_types
        },
        **{key: [docs.get(m, empty).get(key, 0) for m in months] for key in scalar_series},
        "blocks": latest.get("blocks", {}),
        "totals": latest.get("totals", {}),
        "updated_at": max(
            (doc["updated_at"] for doc in docs.values() if doc.get("updated_at")), default=None
        ),
    }


def get_stats_summary(db: Database, force: bool = False) -> dict[str, Any]:
    """Return the stats summary, first updating the stored histograms if they are stale."""
    latest = db[STATS_COLLECTION].find_one(sort=[("_id", -1)]) or {}
    updated_at = latest.get("updated_at") if "totals" in latest else None
    # pymongo returns naive datetimes (in UTC) unless the client is timezone-aware
    if updated_at is not None and updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=tz.utc)
    stale = updated_at is None or datetime.now(tz=tz.utc) - updated_at > STATS_REFRESH_INTERVAL
    if force or stale:
        update_deployment_stats(db)
    return build_stats_summary(db)
