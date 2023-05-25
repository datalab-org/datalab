from typing import Optional

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasBlocks, HasOwner
from pydatalab.models.utils import HumanReadableIdentifier


class Collection(Entry, HasOwner, HasBlocks):

    type: str = Field("collections", const="collections", pattern="^collections$")

    collection_id: HumanReadableIdentifier
    """A short human-readable/usable name for the collection."""

    title: Optional[str]
    """A descriptive title for the collection."""

    description: Optional[str]
    """A description of the collection, either in plain-text or a markup language."""

    num_items: Optional[int] = Field(None)
    """Inlined number of items associated with this collection."""
