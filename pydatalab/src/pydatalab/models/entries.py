import abc
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import (
    JSON_ENCODERS,
    EntryReference,
    IsoformatDateTime,
    PyObjectId,
)


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

    last_modified: Optional[IsoformatDateTime] = None
    """The timestamp at which the entry was last modified."""

    relationships: Optional[List[TypedRelationship]] = None
    """A list of related entries and their types."""

    @root_validator(pre=True)
    def check_id_names(cls, values):
        """Slightly upsetting hack: this case *should* be covered by the pydantic setting for
        populating fields by alias names.
        """
        if "_id" in values:
            values["immutable_id"] = values.pop("_id")

        return values

    def to_reference(self, additional_fields: Optional[List[str]] = None) -> "EntryReference":
        """Populate an EntryReference model from this entry, selecting additional fields to inline.

        Parameters:
            additional_fields: A list of fields to inline in the reference.

        """
        if additional_fields is None:
            additional_fields = []

        data = {
            "type": self.type,
            "item_id": getattr(self, "item_id", None),
            "immutable_id": getattr(self, "immutable_id", None),
        }
        data.update({field: getattr(self, field, None) for field in additional_fields})

        return EntryReference(**data)

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "ignore"
