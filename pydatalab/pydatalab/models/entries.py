import abc
import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import JSON_ENCODERS, PyObjectId


class Entry(BaseModel, abc.ABC):
    """An Entry is an abstract base class for any model that can be
    deserialized and stored in the database.

    """

    type: str = None
    """The resource type of the entry."""

    immutable_id: PyObjectId = Field(
        None,
        title="Immutable ID",
        alias="_id",
    )
    """The immutable database ID of the entry."""

    last_modified: Optional[datetime.datetime] = None
    """The timestamp at which the entry was last modified."""

    relationships: Optional[List[TypedRelationship]] = None
    """A list of related entries and their types."""

    revision: int = 1
    """The revision number of the entry."""

    revisions: Optional[Dict[int, Any]] = None
    """An optional mapping from old revision numbers to the model state at that revision."""

    @validator("type", pre=True)
    def set_default_type(cls, v):
        if not v:
            v = cls.__class__.__name__.lower() + "s"
        return v

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "forbid"
