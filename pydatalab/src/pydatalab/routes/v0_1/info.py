"""This submodule defines introspective info endpoints of the API."""

import json
from datetime import datetime
from functools import lru_cache

from flask import Blueprint, jsonify, request
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from pydatalab import __version__
from pydatalab.apps import BLOCK_TYPES
from pydatalab.config import CONFIG, FEATURE_FLAGS, FeatureFlags
from pydatalab.models import Collection, Person
from pydatalab.models.items import Item
from pydatalab.mongo import flask_mongo

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


class Data(BaseModel):
    id: str
    type: str
    attributes: Attributes


class JSONAPIResponse(BaseModel):
    data: Data | list[Data]
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
    features: FeatureFlags = FEATURE_FLAGS

    @field_validator("maintainer", mode="before")
    @classmethod
    def strip_maintainer_fields(cls, v):
        if isinstance(v, Person):
            return MetaPerson(contact_email=v.contact_email, display_name=v.display_name)
        return v

    @model_validator(mode="after")
    def ensure_features_serialization(self):
        """Ensure features are properly serialized for frontend consumption."""
        if hasattr(self.features, "model_dump"):
            features_dict = self.features.model_dump()
        elif hasattr(self.features, "dict"):
            features_dict = self.features.dict()
        else:
            features_dict = self.features

        if not isinstance(self.features, FeatureFlags):
            self.features = FeatureFlags(**features_dict)
        return self


@lru_cache(maxsize=1)
def _get_deployment_metadata_once() -> dict:
    identifier_prefix = CONFIG.IDENTIFIER_PREFIX
    metadata = (
        CONFIG.DEPLOYMENT_METADATA.model_dump(exclude_none=True)
        if CONFIG.DEPLOYMENT_METADATA
        else {}
    )
    metadata.update({"identifier_prefix": identifier_prefix})
    return metadata


@INFO.route("/info", methods=["GET"])
def get_info():
    """Returns the runtime metadata for the deployment, e.g.,
    versions, features and so on.

    """
    metadata = _get_deployment_metadata_once().copy()
    info = Info(**metadata)

    return (
        jsonify(
            json.loads(
                JSONAPIResponse(
                    data=Data(id="/", type="info", attributes=info),
                    meta=Meta(query=request.query_string.decode() if request.query_string else ""),
                    links=Links(self=request.url),
                ).model_dump_json()
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
            ).model_dump_json()
        )
    )


def get_all_items_models():
    return Item.__subclasses__()


def generate_schemas():
    schemas: dict[str, dict] = {}

    for model_class in get_all_items_models() + [Collection]:
        model_type = model_class.model_json_schema()["properties"]["type"]["default"]

        schemas[model_type] = model_class.model_json_schema(by_alias=False)

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
            ).model_dump_json()
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
            ).model_dump_json()
        )
    )
