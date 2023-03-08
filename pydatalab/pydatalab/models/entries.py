import abc
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import (
    JSON_ENCODERS,
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
    Refcode,
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


class EntryReference(BaseModel):
    """A reference to a database entry by ID and type.

    Can include additional arbitarary metadata useful for
    inlining the item data.

    """

    type: str
    immutable_id: Optional[PyObjectId]
    item_id: Optional[HumanReadableIdentifier]
    refcode: Optional[Refcode]

    @root_validator
    def check_id_fields(cls, values):
        """Check that only one of the possible identifier fields is provided."""
        id_fields = ("immutable_id", "item_id", "refcode")

        # Temporarily remove refcodes from the list of fields to check
        # until it is fully implemented
        if values.get("refcode") is not None:
            values["refcode"] = None
        if all(values.get(f) is None for f in id_fields):
            raise ValueError(f"Must provide at least one of {id_fields!r}")

        if sum(1 for f in id_fields if values.get(f) is not None) > 1:
            raise ValueError("Must provide only one of {id_fields!r}")

        return values

    class Config:
        extra = "allow"
