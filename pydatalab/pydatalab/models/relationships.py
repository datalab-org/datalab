from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


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


class KnownType(str, Enum):
    """An enumeration of the types of entry known by this implementation, should be made dynamic in the future."""

    SAMPLE = "samples"
    BLOCK = "block"
    FILE = "files"
    STARTING_MATERIAL = "starting_materials"


class TypedRelationship(BaseModel):

    description: Optional[str] = Field(
        None,
        description="A description of the relationship.",
    )

    relation: RelationshipType = Field(
        description="The type of relationship between the two items. If the type is 'other', then a human-readable description should be provided."
    )

    type: KnownType = Field(description="The type of the related resource.")

    item_id: str = Field(description="The ID of the entry that is related to this entry.")

    @validator("relation")
    def check_for_description(cls, v, values):
        if v == RelationshipType.OTHER and values.get("description") is None:
            raise ValueError(
                f"A description must be provided if the relationship type is {RelationshipType.OTHER.value!r}."
            )

        return v
