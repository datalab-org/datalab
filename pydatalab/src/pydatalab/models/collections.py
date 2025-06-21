from pydantic import Field, root_validator

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasBlocks, HasOwner
from pydatalab.models.utils import HumanReadableIdentifier


class Collection(Entry, HasOwner, HasBlocks):
    type: str = Field("collections", const="collections", pattern="^collections$")

    collection_id: HumanReadableIdentifier = Field(None)
    """A short human-readable/usable name for the collection."""

    title: str | None
    """A descriptive title for the collection."""

    description: str | None
    """A description of the collection, either in plain-text or a markup language."""

    num_items: int | None = Field(None)
    """Inlined number of items associated with this collection."""

    @root_validator
    def check_ids(cls, values):
        if not any(values.get(k) is not None for k in ("collection_id", "immutable_id")):
            raise ValueError("Collection must have at least collection_id or immutable_id")

        return values
