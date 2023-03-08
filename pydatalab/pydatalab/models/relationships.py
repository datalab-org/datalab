from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, root_validator, validator

from pydatalab.models.utils import (
    HumanReadableIdentifier,
    KnownType,
    PyObjectId,
    Refcode,
)


class RelationshipType(str, Enum):
    """An enumeration of the possible types of relationship between two entries.

    ```mermaid
    classDiagram
    class entryC
    entryC --|> entryA: parent
    entryC ..|> entryD
    entryA <..> entryD: sibling
    entryA --|> entryB : child
    ```

    """

    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    PARTHOOD = "is_part_of"
    OTHER = "other"


class TypedRelationship(BaseModel):

    description: Optional[str] = Field(
        None,
        description="A description of the relationship.",
    )

    relation: RelationshipType = Field(
        description="The type of relationship between the two items. If the type is 'other', then a human-readable description should be provided."
    )

    type: KnownType = Field(description="The type of the related resource.")

    immutable_id: Optional[PyObjectId] = Field(
        description="The immutable ID of the entry that is related to this entry."
    )

    item_id: Optional[HumanReadableIdentifier] = Field(
        description="The ID of the entry that is related to this entry."
    )

    refcode: Optional[Refcode] = Field(
        description="The refcode of the entry that is related to this entry."
    )

    @validator("relation")
    def check_for_description(cls, v, values):
        if v == RelationshipType.OTHER and values.get("description") is None:
            raise ValueError(
                f"A description must be provided if the relationship type is {RelationshipType.OTHER.value!r}."
            )

        return v

    @root_validator
    def check_id_fields(cls, values):
        """Check that only one of the possible identifier fields is provided."""
        id_fields = ("immutable_id", "item_id", "refcode")
        if all(values[f] is None for f in id_fields):
            raise ValueError(f"Must provide at least one of {id_fields!r}")
        if sum(1 for f in id_fields if values[f] is not None) > 1:
            raise ValueError("Must provide only one of {id_fields!r}")

        return values
