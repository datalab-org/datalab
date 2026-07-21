from typing import Literal

from pydantic import (
    model_validator,
)

from pydatalab.models.blocks import HasBlocks
from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasOwner
from pydatalab.models.utils import HumanReadableIdentifier


class Collection(Entry, HasOwner, HasBlocks):
    type: Literal["collections"] = "collections"

    collection_id: HumanReadableIdentifier
    """A short human-readable/usable name for the collection."""

    title: str | None = None
    """A descriptive title for the collection."""

    description: str | None = None
    """A description of the collection, either in plain-text or a markup language."""

    num_items: int | None = None
    """Inlined number of items associated with this collection."""

    @model_validator(mode="before")
    @classmethod
    def check_ids(cls, values):
        if not any(values.get(k) is not None for k in ("collection_id", "immutable_id")):
            raise ValueError("Collection must have at least collection_id or immutable_id")

        return values
