import abc
import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, root_validator, validator

from pydatalab.models.entries import Entry
from pydatalab.models.people import Person, PyObjectId
from pydatalab.models.utils import JSON_ENCODERS


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    type: str = Field(description="The resource type of the item.")

    last_modified: Optional[datetime.datetime] = Field(
        description="The timestamp at which this item was last modified."
    )

    creator_ids: List[PyObjectId] = Field(
        [], description="The database IDs of the user(s) who created the item."
    )

    creators: Optional[List[Person]] = Field(
        None, description="Inlined info for the people associated with this item."
    )

    parent_items: List[str] = Field(
        default=[], description="Items from which this sample is derived"
    )

    child_items: List[str] = Field(
        default=[], description="Items that are derived from this sample"
    )

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

    class Config:
        # Do not let arbitrary data be added alongside this sample
        # extra = "forbid"
        json_encoders = JSON_ENCODERS

    @validator("last_modified", pre=True)
    def cast_to_datetime(cls, v):
        if isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)

        return v

    @validator("file_ObjectIds", each_item=True, pre=True)
    def string_objectids(cls, v):
        return str(v)

    @root_validator(pre=True)
    def pop_mongo_objectid(cls, values):
        if "_id" in values:
            values.pop("_id")

        return values
