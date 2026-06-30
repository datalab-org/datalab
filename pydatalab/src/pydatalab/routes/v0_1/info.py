"""This submodule defines introspective info endpoints of the API."""

import json
from datetime import datetime
from datetime import timedelta as td
from datetime import timezone as tz
from functools import lru_cache
from typing import Any, Generic, TypeVar

from flask import Blueprint, jsonify, request
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from pydatalab import __version__
from pydatalab.apps import BLOCK_TYPES
from pydatalab.config import CONFIG
from pydatalab.feature_flags import FEATURE_FLAGS, FeatureFlags
from pydatalab.models import BUILTIN_ITEM_TYPES, ITEM_MODELS, ITEM_SCHEMAS, Person
from pydatalab.models.schema_hints import DatalabModelExtra
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only

from ._version import __api_version__

INFO = Blueprint("info", __name__)


class Attributes(BaseModel):
    model_config = ConfigDict(extra="allow")


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = ""
    api_version: str = __api_version__
    available_api_versions: list[str] = [__api_version__]
    server_version: str = __version__
    datamodel_version: str = __version__


class Links(BaseModel):
    self: AnyUrl
    model_config = ConfigDict(extra="allow")


AttributesT = TypeVar("AttributesT")


class Data(BaseModel, Generic[AttributesT]):
    id: str
    type: str
    attributes: AttributesT
    """The attributes payload, serialized as whatever concrete type the envelope is
    parametrised with (e.g. ``Data[Info]``) so subclass fields are not stripped."""


class JSONAPIResponse(BaseModel, Generic[AttributesT]):
    data: Data[AttributesT] | list[Data[AttributesT]]
    meta: Meta
    links: Links | None = None


class MetaPerson(BaseModel):
    display_name: str | None = None
    contact_email: str


class Info(Attributes, Meta):
    maintainer: MetaPerson | None = None
    issue_tracker: AnyUrl | None = None
    homepage: AnyUrl | None = None
    source_repository: AnyUrl | None = None
    identifier_prefix: str
    features: FeatureFlags | None = None
    max_upload_bytes: int

    @field_validator("maintainer", mode="before")
    @classmethod
    def strip_maintainer_fields(cls, v):
        if isinstance(v, Person):
            return MetaPerson(contact_email=v.contact_email, display_name=v.display_name)
        return v


@lru_cache(maxsize=1)
def _get_deployment_metadata_once() -> dict:
    identifier_prefix = CONFIG.IDENTIFIER_PREFIX
    metadata = (
        CONFIG.DEPLOYMENT_METADATA.model_dump(exclude_none=True)
        if CONFIG.DEPLOYMENT_METADATA
        else {}
    )
    metadata.update(
        {
            "identifier_prefix": identifier_prefix,
            "max_upload_bytes": CONFIG.MAX_CONTENT_LENGTH,
            "features": FEATURE_FLAGS,
        }
    )
    return metadata


@INFO.route("/info", methods=["GET"])
def get_info():
    """Returns the runtime metadata for the deployment, e.g.,
    versions, features and so on.

    """

    response_data = JSONAPIResponse[Info](
        data=Data(id="/", type="info", attributes=Info(**_get_deployment_metadata_once())),
        meta=Meta(query=request.query_string.decode() if request.query_string else ""),
        links=Links(self=request.url),
    )

    return (
        jsonify(json.loads(response_data.model_dump_json())),
        200,
    )


@INFO.route("/info/stats", methods=["GET"])
@active_users_or_get_only
def get_stats():
    """Returns a dictionary of counts of each entry type in the deployment"""

    user_count = flask_mongo.db.users.count_documents({})
    sample_count = flask_mongo.db.items.count_documents({"type": "samples"})
    cell_count = flask_mongo.db.items.count_documents({"type": "cells"})

    return (
        jsonify({"counts": {"users": user_count, "samples": sample_count, "cells": cell_count}}),
        200,
    )


@INFO.route("/info/blocks", methods=["GET"])
def list_block_types():
    """Returns a list of all blocks implemented in this server."""
    return jsonify(
        json.loads(
            JSONAPIResponse[dict[str, Any]](
                data=[
                    Data(
                        id=block_type,
                        type="block_type",
                        attributes={
                            "name": getattr(block, "name", ""),
                            "description": getattr(block, "description", ""),
                            "version": getattr(block, "version", __version__),
                            "accepted_file_extensions": getattr(
                                block, "accepted_file_extensions", []
                            ),
                            "multi_file": getattr(block, "multi_file", False),
                        },
                    )
                    for block_type, block in BLOCK_TYPES.items()
                ],
                meta=Meta(query=request.query_string.decode() if request.query_string else ""),
            ).model_dump_json()
        )
    )


def _get_base_type(item_type: str) -> str | None:
    """Return the built-in type that this item type inherits from, or None if it is a built-in.

    Uses issubclass against the registered built-in models, so it works regardless of
    whether the plugin's intermediate base class (e.g. Sample) appears in the MRO
    (which depends on the installed version of the plugin package).
    The most-derived built-in base is returned.
    """
    model = ITEM_MODELS.get(item_type)
    if model is None or item_type in BUILTIN_ITEM_TYPES:
        return None
    best_type: str | None = None
    best_model: type | None = None
    for builtin_type, builtin_model in ITEM_MODELS.items():
        if builtin_type not in BUILTIN_ITEM_TYPES:
            continue
        if issubclass(model, builtin_model):
            # Prefer the most specific (most-derived) built-in base.
            if best_model is None or issubclass(builtin_model, best_model):
                best_type = builtin_type
                best_model = builtin_model
    return best_type


def _get_model_schema_extra(item_type: str) -> dict:
    """Return the `json_schema_extra` dict declared on the model's config, if any."""
    model = ITEM_MODELS.get(item_type)
    if model is None:
        return {}
    extra = model.model_config.get("json_schema_extra") or {}
    if callable(extra):
        return {}
    return extra


def _type_attributes(item_type: str, schema: dict) -> dict:
    """Build the attributes dict for a single item type in the /info/types response."""
    extra = DatalabModelExtra(
        **{k: v for k, v in _get_model_schema_extra(item_type).items() if k.startswith("datalab_")}
    )
    return {
        "version": __version__,
        "api_version": __api_version__,
        "schema": schema,
        "title": schema.get("title"),
        "base_type": _get_base_type(item_type),
        "hidden_fields": extra.datalab_ui_hidden_fields or [],
        "ui_color": extra.datalab_ui_color,
    }


@INFO.route("/info/types", methods=["GET"])
def list_supported_types():
    """Returns a list of supported schemas."""

    return jsonify(
        json.loads(
            JSONAPIResponse[dict[str, Any]](
                data=[
                    Data(
                        id=item_type,
                        type="item_type",
                        attributes=_type_attributes(item_type, schema),
                    )
                    for item_type, schema in ITEM_SCHEMAS.items()
                ],
                meta=Meta(query=request.query_string.decode() if request.query_string else ""),
            ).model_dump_json()
        )
    )


@INFO.route("/info/types/<string:item_type>", methods=["GET"])
def get_schema_type(item_type):
    """Returns the schema of the given type."""
    if item_type not in ITEM_SCHEMAS:
        return jsonify(
            {"status": "error", "detail": f"Item type {item_type} not found for this deployment"}
        ), 404

    return jsonify(
        json.loads(
            JSONAPIResponse[dict[str, Any]](
                data=Data(
                    id=item_type,
                    type="item_type",
                    attributes=_type_attributes(item_type, ITEM_SCHEMAS[item_type]),
                ),
                meta=Meta(query=request.query_string.decode() if request.query_string else ""),
            ).model_dump_json()
        )
    )


@lru_cache(maxsize=3)
def _fetch_activity_data(months: int, cache_date: str):
    """Fetch activity data - cache_date forces daily refresh."""
    end_date = datetime.now(tz=tz.utc).replace(tzinfo=None)
    start_date = end_date - td(days=30 * months)

    pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    activity_data = list(flask_mongo.db.items.aggregate(pipeline))

    return {date_entry["_id"]: date_entry["count"] for date_entry in activity_data}


@INFO.route("/info/user-activity", methods=["GET"])
@active_users_or_get_only
def get_combined_activity():
    """Get combined activity data for all users."""

    months = int(request.args.get("months", 12))
    cache_date = datetime.now(tz=tz.utc).date().isoformat()

    result = _fetch_activity_data(months, cache_date)

    return jsonify({"status": "success", "data": result}), 200
