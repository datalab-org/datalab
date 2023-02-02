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

    item_id: HumanReadableIdentifier
    """A unique, human-readable identifier for the entry."""

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""

    description: Optional[str]
    """A description of the item, either in plain-text or a markup language."""

    date: Optional[IsoformatDateTime]
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: Optional[str]
    """An optional human-readable/usable name for the entry."""

    blocks_obj: Dict[str, Any] = Field({})
    """A mapping from block ID to block data."""

    display_order: List[str] = Field([])
    """The order in which to display block data in the UI."""

    files: Optional[List[str]]
    """Any files attached to this sample."""

    file_ObjectIds: List[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""
