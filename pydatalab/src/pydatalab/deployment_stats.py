# This file was edited with the assistance of an AI model and requires human review from the contributor.
"""Historical usage statistics for a deployment.

Monthly histograms of new entries (items, users, files, collections, ...) are
stored in their own database collection (`deployment_stats`), with one
document per calendar month. The collection is updated incrementally: only the
most recent stored month (which may have been partial when last computed) and
any subsequent months are recomputed, using the creation time embedded in each
document's `ObjectId`, so an update only scans documents created since then.

Months that have been closed off are therefore a historical record of what was
created in that month; later deletions do not rewrite history.

"""

from collections import defaultdict
from datetime import datetime, timedelta
from datetime import timezone as tz
from threading import Lock
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from pydatalab.logger import LOGGER

STATS_COLLECTION = "deployment_stats"
"""The name of the database collection that stores the monthly histograms."""

STATS_REFRESH_INTERVAL = timedelta(hours=6)
"""How long a computed set of histograms (and the served summary) is considered fresh."""

EARLIEST_DATE = datetime(2019, 1, 1, tzinfo=tz.utc)
"""Entries with ObjectIds that claim to be older than this, or to be from the future
(e.g., hand-crafted IDs such as `000000000000000000000000`), are excluded from the histograms."""

_MONTH_FORMAT = "%Y-%m"

_cache_lock = Lock()
_cached_summary: dict[str, Any] | None = None
_cached_at: datetime | None = None


def _now() -> datetime:
    return datetime.now(tz=tz.utc)


def _next_month(dt: datetime) -> datetime:
    return datetime(dt.year + dt.month // 12, dt.month % 12 + 1, 1, tzinfo=tz.utc)


def _month_key(dt: datetime) -> str:
    return dt.strftime(_MONTH_FORMAT)


def _created_since(since: datetime | None) -> dict:
    """Match plausible ObjectIds created at or after `since` (or `EARLIEST_DATE`)."""
    since = max(since or EARLIEST_DATE, EARLIEST_DATE)
    return {
        "_id": {
            "$type": "objectId",
            "$gte": ObjectId.from_datetime(since),
            "$lt": ObjectId.from_datetime(_now() + timedelta(days=1)),
        }
    }


def _group_by_month(extra_keys: dict | None = None, accumulators: dict | None = None) -> dict:
    group_id: dict[str, Any] = {
        "month": {"$dateToString": {"format": _MONTH_FORMAT, "date": {"$toDate": "$_id"}}}
    }
    if extra_keys:
        group_id.update(extra_keys)
    return {"$group": {"_id": group_id, "count": {"$sum": 1}, **(accumulators or {})}}


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
    match = {"$match": _created_since(since)}

    for doc in db.items.aggregate([match, _group_by_month(extra_keys={"type": "$type"})]):
        item_type = doc["_id"].get("type") or "unknown"
        months[doc["_id"]["month"]]["items"][item_type] = doc["count"]

    # Anyone who created an item in a given month counts as active in that month
    for doc in db.items.aggregate(
        [
            match,
            {"$unwind": "$creator_ids"},
            _group_by_month(accumulators={"users": {"$addToSet": "$creator_ids"}}),
        ]
    ):
        active_users[doc["_id"]["month"]].update(str(u) for u in doc["users"] if u is not None)

    for doc in db.users.aggregate([match, _group_by_month()]):
        months[doc["_id"]["month"]]["users"] = doc["count"]

    for doc in db.collections.aggregate([match, _group_by_month()]):
        months[doc["_id"]["month"]]["collections"] = doc["count"]

    for doc in db.files.aggregate(
        [match, _group_by_month(accumulators={"bytes": {"$sum": {"$ifNull": ["$size", 0]}}})]
    ):
        months[doc["_id"]["month"]]["files"] = doc["count"]
        months[doc["_id"]["month"]]["file_bytes"] = doc["bytes"]

    # Item versions record saves (and their authors) and so capture activity on existing items
    for doc in db.item_versions.aggregate(
        [match, _group_by_month(accumulators={"users": {"$addToSet": "$user_id"}})]
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
    now = _now()

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
    if since is not None:
        month = since
        while month <= now:
            histograms.setdefault(_month_key(month), _empty_month())
            month = _next_month(month)

    written = 0
    for month, stats in histograms.items():
        collection.replace_one(
            {"_id": month},
            {"_id": month, **stats, "updated_at": now},
            upsert=True,
        )
        written += 1

    LOGGER.info("Updated %d monthly entries in %s (since %s)", written, STATS_COLLECTION, since)
    return written


def _needs_update(db: Database) -> bool:
    latest = db[STATS_COLLECTION].find_one(sort=[("_id", -1)])
    if latest is None:
        return True
    updated_at = latest.get("updated_at")
    if updated_at is None:
        return True
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=tz.utc)
    return _now() - updated_at > STATS_REFRESH_INTERVAL


def _block_type_counts(db: Database) -> dict[str, int]:
    """Count the blocks of each type currently attached to items."""
    pipeline = [
        {"$match": {"blocks_obj": {"$type": "object"}}},
        {"$project": {"blocks": {"$objectToArray": "$blocks_obj"}}},
        {"$unwind": "$blocks"},
        {"$group": {"_id": "$blocks.v.blocktype", "count": {"$sum": 1}}},
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
    now = _now()

    months: list[str] = []
    if docs:
        month = datetime.strptime(min(docs), _MONTH_FORMAT).replace(tzinfo=tz.utc)
        while month <= now:
            months.append(_month_key(month))
            month = _next_month(month)

    item_types = sorted({t for doc in docs.values() for t in doc.get("items", {})})
    scalar_series = [key for key in _empty_month() if key != "items"]

    blocks = _block_type_counts(db)
    totals = _current_totals(db)
    totals["blocks"] = sum(blocks.values())

    empty: dict[str, Any] = {}
    return {
        "months": months,
        "items": {
            item_type: [docs.get(m, empty).get("items", {}).get(item_type, 0) for m in months]
            for item_type in item_types
        },
        **{key: [docs.get(m, empty).get(key, 0) for m in months] for key in scalar_series},
        "blocks": blocks,
        "totals": totals,
        "updated_at": max(
            (doc["updated_at"] for doc in docs.values() if doc.get("updated_at")), default=None
        ),
    }


def get_stats_summary(db: Database, force: bool = False) -> dict[str, Any]:
    """Return the (cached) stats summary, updating the stored histograms if they are stale.

    The summary is cached in memory for `STATS_REFRESH_INTERVAL`, so repeated requests
    do not touch the database.

    """
    global _cached_summary, _cached_at

    with _cache_lock:
        now = _now()
        if (
            not force
            and _cached_summary is not None
            and _cached_at is not None
            and now - _cached_at < STATS_REFRESH_INTERVAL
        ):
            return _cached_summary

        if force or _needs_update(db):
            update_deployment_stats(db)

        _cached_summary = build_stats_summary(db)
        _cached_at = now
        return _cached_summary


def clear_stats_cache() -> None:
    """Clear the in-memory cache of the stats summary."""
    global _cached_summary, _cached_at
    with _cache_lock:
        _cached_summary = None
        _cached_at = None
