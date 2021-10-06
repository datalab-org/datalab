import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class Item(BaseModel):
    """The generic model for data types that will be exposed with their own named endpoints."""

    type: str = Field(description="The resource type of the item.")

    date: datetime.datetime = Field(description="The creation timestamp of the item.")

    last_modified: Optional[datetime.datetime] = Field(
        description="The timestamp at which this item was last modified."
    )

    name: Optional[str] = Field(description="A human-readable/usable name for the item.")

    description: Optional[str] = Field(
        description="A description of the item, either in plain-text or a markup language."
    )

    nblocks: Optional[int] = Field(0, description="The number of blocks attached to this item.")

    blocks: List[Dict[Any, Any]] = Field([], description="The blocks attached to this item.")

    blocks_obj: Dict[str, Any] = Field({}, description="A mapping from block ID to block data.")

    display_order: List[str] = Field(
        [], description="The order in which to display block data in the UI."
    )

    files: Optional[List[str]] = Field(description="Any files attached to this sample.")

    file_ObjectIds: List[str] = Field(
        [], description="Links to object IDs of files stored within the database."
    )

    class Config:
        # Do not let arbitrary data be added alongside this sample
        extra = "forbid"

    @validator("date", "last_modified", pre=True)
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


def test():
    print("this is a test")
    print("test2")
