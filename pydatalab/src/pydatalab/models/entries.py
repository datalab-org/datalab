import abc

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import (
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

    immutable_id: PyObjectId | None = Field(
        None,
        title="Immutable ID",
        alias="_id",
        json_schema_extra={"format": "uuid"},
    )
    """The immutable database ID of the entry."""

    last_modified: IsoformatDateTime | None = None
    """The timestamp at which the entry was last modified."""

    relationships: list[TypedRelationship] = Field(default_factory=list)
    """A list of related entries and their types."""

    @model_validator(mode="before")
    @classmethod
    def check_id_names(cls, values):
        """Slightly upsetting hack: this case *should* be covered by the pydantic setting for
        populating fields by alias names.
        """
        if "_id" in values:
            values["immutable_id"] = values.pop("_id")

        return values

    @model_validator(mode="after")
    def validate_relationships(self):
        """Ensure relationships is always a list."""
        if self.relationships is None:
            self.relationships = []
        return self

    def to_reference(self, additional_fields: list[str] | None = None) -> "EntryReference":
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

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_serializer("immutable_id", when_used="json")
    def serialize_object_id(self, value):
        return str(value) if value else None

    @field_serializer("last_modified", when_used="json")
    def serialize_datetime(self, value):
        return value.isoformat() if value else None
