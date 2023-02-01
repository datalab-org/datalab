"""This submodule defines introspective info endpoints of the API."""

import json
from datetime import datetime
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Union

from flask import jsonify, request
from pydantic import AnyUrl, BaseModel, Field, validator

from pydatalab import __version__
from pydatalab.models import Person

from ._version import __api_version__


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
    links: Links


class MetaPerson(BaseModel):
    dislay_name: Optional[str]
    contact_email: str


class Info(Attributes, Meta):

    maintainer: Optional[MetaPerson]
    issue_tracker: Optional[AnyUrl]
    homepage: Optional[AnyUrl]
    source_repository: Optional[AnyUrl]

    @validator("maintainer")
    def strip_maintainer_fields(cls, v):
        if isinstance(v, Person):
            return MetaPerson(contact_email=v.contact_email, display_name=v.display_name)
        return v


@lru_cache(maxsize=1)
def _get_deployment_metadata_once() -> Dict:
    from pydatalab.config import CONFIG

    return CONFIG.DEPLOYMENT_METADATA.dict(exclude_none=True) if CONFIG.DEPLOYMENT_METADATA else {}


def get_info():

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


ENDPOINTS: Dict[str, Callable] = {
    "/info/": get_info,
}
