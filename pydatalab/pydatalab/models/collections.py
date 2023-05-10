from typing import List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry, EntryReference
from pydatalab.models.people import Person
from pydatalab.models.traits import HasOwner
from pydatalab.models.utils import HumanReadableIdentifier, PyObjectId


class Collection(Entry, HasOwner):

    type: str = Field("collections", const="collections", pattern="^collections$")

    collection_id: HumanReadableIdentifier
    """A short human-readable/usable name for the collection."""

    title: Optional[str]
    """A descriptive title for the collection."""

    description: Optional[str]
    """A description of the collection, either in plain-text or a markup language."""

    num_items: Optional[int] = Field(None)
    """Inlined number of items associated with this collection."""


class CollectionReference(EntryReference):

    collection_id: Optional[str]
    """An human-readable/usable name for the collection."""

    type: str = Field("collections", const="collections", pattern="^collections$")
