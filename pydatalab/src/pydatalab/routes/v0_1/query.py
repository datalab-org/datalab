"""Advanced-search routes.

Searches take a filter written in the
[OPTIMADE filter language](https://www.optimade.org/specification/latest/#api-filtering-format-specification),
passed in the ``filter`` URL query parameter, e.g.
``GET /query/samples?filter=name CONTAINS "LFP"&sort=-date&limit=50``.
Filters are compiled by :mod:`pydatalab.routes.v0_1.query_filter`; the queryable properties of
each type come from :mod:`pydatalab.routes.v0_1.query_schema`.
"""

import bson.errors
import pymongo.errors
from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.logger import LOGGER
from pydatalab.login import UserRole
from pydatalab.models.people import AccountStatus
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions
from pydatalab.routes.v0_1.query_filter import InvalidFilter, compile_filter
from pydatalab.routes.v0_1.query_schema import (
    OPERATORS,
    SEARCHABLE_TYPES,
    VALUE_TYPE_EDITORS,
    type_field_registry,
    type_label,
    types_for_table,
)

QUERY = Blueprint("query", __name__)

DEFAULT_LIMIT = 50
MAX_LIMIT = 1000
# Largest value MongoDB accepts for `$skip`/`$limit` (a signed 64-bit integer).
_MAX_INT64 = 2**63 - 1

_GROUP_ORDER = ["Basic", "Chemistry", "Cell", "Synthesis", "Provenance"]

# Searches only return what identifies each match: the webapp shows the matching rows from
# the table data it already has, so nothing else needs to be sent (or exposed).
_ID_PROJECTIONS = {
    "items": {"_id": 0, "item_id": 1, "type": 1},
    "collections": {"_id": 0, "collection_id": 1},
}
_DEFAULT_ID_PROJECTION = {"_id": {"$toString": "$_id"}}


class QueryError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


@QUERY.before_request
@active_users_or_get_only
def _(): ...


@QUERY.errorhandler(QueryError)
def _query_error(exc: QueryError):
    return jsonify({"status": "error", "message": exc.message}), exc.status


def _is_admin() -> bool:
    """Same check as :func:`pydatalab.permissions.admin_only`."""
    return (
        current_user.is_authenticated
        and current_user.role == UserRole.ADMIN
        and current_user.account_status == AccountStatus.ACTIVE
    )


def _searchable_type(type_id: str) -> dict:
    entry = SEARCHABLE_TYPES.get(type_id)
    # Admin-only types are reported as unknown to everyone else, so as not to reveal them.
    if (
        not entry
        or (entry["view"].get("admin_only") and not _is_admin())
        or not type_field_registry(type_id)
    ):
        raise QueryError(404, f"Unknown searchable type {type_id!r}")
    return entry


def _int_arg(name: str, default: int) -> int:
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        value = -1
    if value < 0 or value > _MAX_INT64:
        raise QueryError(400, f"{name} must be a non-negative integer")
    return value


def _sort(entry: dict, registry: dict) -> dict:
    """Parse `sort`: comma-separated property names, each prefixed by `-` for descending."""
    raw = request.args.get("sort")
    spec: list[tuple[str, int]] = []
    if raw:
        for token in (t.strip() for t in raw.split(",")):
            name = token[1:] if token.startswith("-") else token
            field = registry.get(name)
            if not field or not field.get("sortable"):
                raise QueryError(400, f"Cannot sort on {name!r}")
            spec.append((field["mongo_path"], -1 if token.startswith("-") else 1))
    else:
        spec.extend(entry["view"].get("default_sort", []))
    sort: dict = {}
    for path, direction in [*spec, ("_id", 1)]:
        sort.setdefault(path, direction)
    return sort


def _operator_entry(op_id: str, field: dict) -> dict:
    op = OPERATORS[op_id]
    entry = {"id": op_id, "label": op["label"], "value_required": op["value_required"]}
    if op["value_required"]:
        default_editor = VALUE_TYPE_EDITORS.get(field.get("value_type", "string"), "text")
        entry["editor"] = field.get("editor_override", {}).get(
            op_id, op.get("editor", default_editor)
        )
    if op_id in field.get("value_schema_override", {}):
        entry["value_schema"] = field["value_schema_override"][op_id]
    return entry


@QUERY.route("/query/types", methods=["GET"])
def get_searchable_types():
    """The types the advanced search of a webapp table (`?data_type=`) can query."""
    types = types_for_table(request.args.get("data_type"), is_admin=_is_admin())
    return jsonify({"status": "success", "types": types})


@QUERY.route("/query/<type_id>/schema", methods=["GET"])
def get_type_schema(type_id: str):
    """The properties of a type that can be used in filters, with their OPTIMADE operators."""
    entry = _searchable_type(type_id)

    def order(item):
        name, field = item
        group = field.get("group", "Other")
        rank = _GROUP_ORDER.index(group) if group in _GROUP_ORDER else len(_GROUP_ORDER)
        return rank, name

    fields = [
        {
            "id": name,
            "label": field["label"],
            "group": field.get("group", "Other"),
            "sortable": bool(field.get("sortable")),
            "groupable": bool(field.get("groupable")),
            "value_type": field.get("value_type", "string"),
            "is_list": bool(field.get("is_list")),
            "operators": [_operator_entry(op_id, field) for op_id in field["operator_ids"]],
        }
        for name, field in sorted(type_field_registry(type_id).items(), key=order)
    ]
    return jsonify(
        {
            "status": "success",
            "type": {"id": type_id, "label": type_label(type_id)},
            "max_depth": 5 if entry["view"].get("resource") == "items" else 0,
            "fields": fields,
        }
    )


def _mine_only() -> bool:
    return request.args.get("mine", "").lower() in ("1", "true")


@QUERY.route("/query/<type_id>", methods=["GET"])
def search(type_id: str):
    """IDs of the entries of a type matching an OPTIMADE `filter`, with `sort`, `limit` and
    `offset`; `mine=true` keeps only entries the current user created."""
    entry = _searchable_type(type_id)
    registry = type_field_registry(type_id)
    limit = _int_arg("limit", DEFAULT_LIMIT)
    if limit > MAX_LIMIT:
        raise QueryError(400, f"limit must be at most {MAX_LIMIT}")
    offset = _int_arg("offset", 0)
    sort = _sort(entry, registry)

    try:
        compiled_filter = compile_filter(request.args.get("filter"), registry)
    except InvalidFilter as exc:
        raise QueryError(400, str(exc)) from exc

    view = entry["view"]
    if view.get("admin_only"):
        # Admins see every entry of these types, as on the corresponding admin pages.
        match: dict = {}
    else:
        match = {"type": type_id} if view["resource"] == "items" else {}
        match.update(get_default_permissions(user_only=False, inherit_from_collections=False))
    if _mine_only():
        if view["resource"] not in ("items", "collections") or current_user.person is None:
            raise QueryError(400, "mine is only supported for items and collections")
        match = {"$and": [match, {"creator_ids": current_user.person.immutable_id}]}
    if compiled_filter:
        match = {"$and": [match, compiled_filter]}

    collection = flask_mongo.db[view["collection"]]
    projection = _ID_PROJECTIONS.get(view["resource"], _DEFAULT_ID_PROJECTION)
    try:
        total = collection.count_documents(match)
        items: list[dict] = []
        if limit:
            pipeline: list[dict] = [
                {"$match": match},
                {"$sort": sort},
                {"$skip": offset},
                {"$limit": limit},
                {"$project": projection},
            ]
            items = list(collection.aggregate(pipeline))
    except (OverflowError, bson.errors.InvalidDocument, pymongo.errors.OperationFailure) as exc:
        # e.g. a number too large for the database in the filter. The database's own message
        # is only logged, so as not to expose its internals.
        LOGGER.info("Advanced search filter could not be run: %s", exc)
        raise QueryError(
            400, "The filter cannot be run, e.g. a number in it may be too large."
        ) from exc

    next_offset = offset + len(items) if limit and offset + len(items) < total else None
    return jsonify(
        {"status": "success", "items": items, "total": total, "next_offset": next_offset}
    )
