"""This submodule defines introspective info endpoints of the API."""

import json
from datetime import datetime
from datetime import timedelta as td
from datetime import timezone as tz
from functools import lru_cache

from flask import Blueprint, jsonify, request
from pydantic import AnyUrl, BaseModel, Field, validator

from pydatalab import __version__
from pydatalab.apps import BLOCK_TYPES
from pydatalab.config import CONFIG
from pydatalab.feature_flags import FEATURE_FLAGS, FeatureFlags
from pydatalab.models import Collection, Person
from pydatalab.models.items import Item
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only

from ._version import __api_version__

INFO = Blueprint("info", __name__)


class Attributes(BaseModel):
    class Config:
        extra = "allow"


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = ""
    api_version: str = __api_version__
    available_api_versions: list[str] = [__api_version__]
    server_version: str = __version__
    datamodel_version: str = __version__


class Links(BaseModel):
    self: AnyUrl

    class Config:
        extra = "allow"


class Data(BaseModel):
    id: str
    type: str
    attributes: Attributes


class JSONAPIResponse(BaseModel):
    data: Data | list[Data]
    meta: Meta
    links: Links | None


class MetaPerson(BaseModel):
    dislay_name: str | None
    contact_email: str


class Info(Attributes, Meta):
    maintainer: MetaPerson | None
    issue_tracker: AnyUrl | None
    homepage: AnyUrl | None
    source_repository: AnyUrl | None
    identifier_prefix: str
    features: FeatureFlags = FEATURE_FLAGS
    max_upload_bytes: int

    @validator("maintainer")
    def strip_maintainer_fields(cls, v):
        if isinstance(v, Person):
            return MetaPerson(contact_email=v.contact_email, display_name=v.display_name)
        return v


@lru_cache(maxsize=1)
def _get_deployment_metadata_once() -> dict:
    identifier_prefix = CONFIG.IDENTIFIER_PREFIX
    metadata = (
        CONFIG.DEPLOYMENT_METADATA.dict(exclude_none=True) if CONFIG.DEPLOYMENT_METADATA else {}
    )
    metadata.update({"identifier_prefix": identifier_prefix})
    metadata.update({"max_upload_bytes": CONFIG.MAX_CONTENT_LENGTH})

    return metadata


@INFO.route("/info", methods=["GET"])
def get_info():
    """Returns the runtime metadata for the deployment, e.g.,
    versions, features and so on.

    """
    metadata = _get_deployment_metadata_once()

    return (
        jsonify(
            json.loads(
                JSONAPIResponse(
                    data=Data(id="/", type="info", attributes=Info(**metadata)),
                    meta=Meta(query=request.query_string),
                    links=Links(self=request.url),
                ).json()
            )
        ),
        200,
    )


@INFO.route("/info/stats", methods=["GET"])
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
            JSONAPIResponse(
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
                        },
                    )
                    for block_type, block in BLOCK_TYPES.items()
                ],
                meta=Meta(query=request.query_string),
            ).json()
        )
    )


def get_all_items_models():
    return Item.__subclasses__()


def generate_schemas():
    schemas: dict[str, dict] = {}

    for model_class in get_all_items_models() + [Collection]:
        model_type = model_class.schema()["properties"]["type"]["default"]

        schemas[model_type] = model_class.schema(by_alias=False)

    return schemas


# Generate once on import
SCHEMAS = generate_schemas()


@INFO.route("/info/types", methods=["GET"])
def list_supported_types():
    """Returns a list of supported schemas."""

    return jsonify(
        json.loads(
            JSONAPIResponse(
                data=[
                    Data(
                        id=item_type,
                        type="item_type",
                        attributes={
                            "version": __version__,
                            "api_version": __api_version__,
                            "schema": schema,
                        },
                    )
                    for item_type, schema in SCHEMAS.items()
                ],
                meta=Meta(query=request.query_string),
            ).json()
        )
    )


@INFO.route("/info/types/<string:item_type>", methods=["GET"])
def get_schema_type(item_type):
    """Returns the schema of the given type."""
    if item_type not in SCHEMAS:
        return jsonify(
            {"status": "error", "detail": f"Item type {item_type} not found for this deployment"}
        ), 404

    return jsonify(
        json.loads(
            JSONAPIResponse(
                data=Data(
                    id=item_type,
                    type="item_type",
                    attributes={
                        "version": __version__,
                        "api_version": __api_version__,
                        "schema": SCHEMAS[item_type],
                    },
                ),
                meta=Meta(query=request.query_string),
            ).json()
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
