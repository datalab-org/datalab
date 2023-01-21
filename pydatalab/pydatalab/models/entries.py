import abc
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import JSON_ENCODERS, CustomDateTime, PyObjectId


class Entry(BaseModel, abc.ABC):
    """An Entry is an abstract base class for any model that can be
    deserialized and stored in the database.

    """

    type: str
    """The resource type of the entry."""

    immutable_id: PyObjectId = Field(
        None,
        title="Immutable ID",
        alias="_id",
    )
    """The immutable database ID of the entry."""

    last_modified: Optional[CustomDateTime] = None
    """The timestamp at which the entry was last modified."""

    relationships: Optional[List[TypedRelationship]] = None
    """A list of related entries and their types."""

    revision: int = 1
    """The revision number of the entry."""

    revisions: Optional[Dict[int, Any]] = None
    """An optional mapping from old revision numbers to the model state at that revision."""

    @root_validator(pre=True)
    def check_id_names(cls, values):
        """Slightly upsetting hack: this case *should* be covered by the pydantic setting for
        populating fields by alias names.
        """
        if "_id" in values:
            values["immutable_id"] = values.pop("_id")

        return values

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "forbid"
