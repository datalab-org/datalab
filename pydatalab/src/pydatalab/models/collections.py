from typing import Literal

from pydantic import (
    Field,
    model_validator,
)

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasBlocks, HasOwner
from pydatalab.models.utils import HumanReadableIdentifier


class Collection(Entry, HasOwner, HasBlocks):
    type: Literal["collections"] = "collections"

    collection_id: HumanReadableIdentifier = Field(
        None, description="A short human-readable/usable name for the collection."
    )

    title: str | None = Field(None, description="A descriptive title for the collection.")

    description: str | None = Field(
        None,
        description="A description of the collection, either in plain-text or a markup language.",
    )

    num_items: int | None = Field(
        None, description="Inlined number of items associated with this collection."
    )

    @model_validator(mode="before")
    @classmethod
    def check_ids(cls, values):
        if not any(values.get(k) is not None for k in ("collection_id", "immutable_id")):
            raise ValueError("Collection must have at least collection_id or immutable_id")

        return values
