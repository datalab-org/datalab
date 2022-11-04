import abc
import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.relationships import TypedRelationship
from pydatalab.models.utils import JSON_ENCODERS


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    description: Optional[str] = Field(
        description="A description of the item, either in plain-text or a markup language."
    )

    date: Optional[datetime.datetime] = Field(
        description="A relevant date supplied for the item (e.g., purchase date, synthesis date)"
    )

    item_id: str = Field("A unique, human-readable identifier for the entry.")

    name: Optional[str] = Field(description="A human-readable/usable name for the entry.")

    blocks_obj: Dict[str, Any] = Field({}, description="A mapping from block ID to block data.")

    display_order: List[str] = Field(
        [], description="The order in which to display block data in the UI."
    )

    relationships: List[TypedRelationship] = Field(
        [], description="List of relationships between this item and others"
    )

    class Config:
        json_encoders = JSON_ENCODERS
