import abc
import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import JSON_ENCODERS, PyObjectId


class Entry(BaseModel, abc.ABC):
    """An Entry is an abstract base class for any model that can be
    deserialized and stored in the database.

    """

    type: str = Field(None, description="The resource type of the entry.")

    immutable_id: PyObjectId = Field(
        None, description="The immutable database ID of the entry.", alias="_id"
    )

    last_modified: Optional[datetime.datetime] = Field(
        description="The timestamp at which the entry was last modified."
    )

    relationships: List[TypedRelationship] = Field(
        [], description="A list of related entries and their types."
    )

    revision: int = Field(1, description="The revision number of the entry.")

    @validator("type", pre=True)
    def set_default_type(cls, v):
        if not v:
            v = cls.__class__.__name__.lower() + "s"
        return v

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "forbid"
