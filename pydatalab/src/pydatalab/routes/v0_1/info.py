"""This submodule defines introspective info endpoints of the API."""

import json
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Union

from flask import Blueprint, jsonify, request
from pydantic import AnyUrl, BaseModel, Field, validator

from pydatalab import __version__
from pydatalab.blocks import BLOCK_TYPES
from pydatalab.config import CONFIG, FEATURE_FLAGS, FeatureFlags
from pydatalab.models import Collection, Person
from pydatalab.models.items import Item
from pydatalab.mongo import flask_mongo

from ._version import __api_version__

INFO = Blueprint("info", __name__)


class Attributes(BaseModel):
    class Config:
        extra = "allow"


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = ""
    api_version: str = __api_version__
    available_api_versions: List[str] = [__api_version__]
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
    data: Union[Data, List[Data]]
    meta: Meta
    links: Optional[Links]


class MetaPerson(BaseModel):
    dislay_name: Optional[str]
    contact_email: str


class Info(Attributes, Meta):
    maintainer: Optional[MetaPerson]
    issue_tracker: Optional[AnyUrl]
    homepage: Optional[AnyUrl]
    source_repository: Optional[AnyUrl]
    identifier_prefix: str
    features: FeatureFlags = FEATURE_FLAGS

    @validator("maintainer")
    def strip_maintainer_fields(cls, v):
        if isinstance(v, Person):
            return MetaPerson(contact_email=v.contact_email, display_name=v.display_name)
        return v


@lru_cache(maxsize=1)
def _get_deployment_metadata_once() -> Dict:
    identifier_prefix = CONFIG.IDENTIFIER_PREFIX
    metadata = (
        CONFIG.DEPLOYMENT_METADATA.dict(exclude_none=True) if CONFIG.DEPLOYMENT_METADATA else {}
    )
    metadata.update({"identifier_prefix": identifier_prefix})
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


def get_all_models():
    return Item.__subclasses__()


@INFO.route("/info/types", methods=["GET"])
def list_supported_types_schemas():
    """Returns a dictionary of supported item types and their schemas."""
    schemas = {cls.__name__.lower(): cls.schema() for cls in get_all_models()}
    schemas["collections"] = Collection.schema()

    return jsonify(schemas)


for model_class in get_all_models():
    model_name = model_class.__name__.lower()

    def make_route(model_class):
        @INFO.route(
            f"/info/types/{model_name}", methods=["GET"], endpoint=f"get_{model_name}_schema"
        )
        def get_model_schema():
            """Returns the JSON schema for the model."""
            return jsonify(model_class.schema())

    make_route(model_class)


@INFO.route("/info/types/collections", methods=["GET"])
def get_collection_schema():
    """Returns the JSON schema for the Collection type."""
    return jsonify(Collection.schema())
