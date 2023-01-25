import abc
from typing import Any, Dict, List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.people import Person
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
)


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    type: str = Field(description="The resource type of the item.")

    creator_ids: List[PyObjectId] = Field(
        [], description="The database IDs of the user(s) who created the item."
    )

    creators: Optional[List[Person]] = Field(
        None, description="Inlined info for the people associated with this item."
    )

    description: Optional[str] = Field(
        description="A description of the item, either in plain-text or a markup language."
    )

    date: Optional[IsoformatDateTime] = Field(
        description="A relevant date supplied for the item (e.g., purchase date, synthesis date)"
    )

    item_id: HumanReadableIdentifier = Field("A unique, human-readable identifier for the entry.")

    name: Optional[str] = Field(description="A human-readable/usable name for the entry.")

    blocks_obj: Dict[str, Any] = Field({}, description="A mapping from block ID to block data.")

    display_order: List[str] = Field(
        [], description="The order in which to display block data in the UI."
    )

    files: Optional[List[str]] = Field(description="Any files attached to this sample.")

    file_ObjectIds: List[PyObjectId] = Field(
        [], description="Links to object IDs of files stored within the database."
    )
