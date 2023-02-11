from typing import List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry, EntryReference
from pydatalab.models.people import Person
from pydatalab.models.utils import HumanReadableIdentifier, PyObjectId


class Collection(Entry):

    type: str = Field("collections", const="collections", pattern="^collections$")

    collection_id: HumanReadableIdentifier
    """A short human-readable/usable name for the collection."""

    title: Optional[str]
    """A descriptive title for the collection."""

    description: Optional[str]
    """A description of the collection, either in plain-text or a markup language."""

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the collection."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this collection."""

    num_items: Optional[int] = Field(None)
    """Inlined number of items associated with this collection."""


class CollectionReference(EntryReference):

    name: str
    """An human-readable/usable name for the collection."""

    type: str = Field("collections", const="collections", pattern="^collections$")
