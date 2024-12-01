from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.people import Person
from pydatalab.models.utils import PyObjectId


class HasOwner(BaseModel):
    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""


class HasRevisionControl(BaseModel):
    revision: int = 1
    """The revision number of the entry."""

    revisions: Optional[Dict[int, Any]] = None
    """An optional mapping from old revision numbers to the model state at that revision."""


class HasBlocks(BaseModel):
    blocks_obj: Dict[str, Any] = Field({})
    """A mapping from block ID to block data."""

    display_order: List[str] = Field([])
    """The order in which to display block data in the UI."""


class IsCollectable(BaseModel):
    """Trait mixin for models that can be
    added to collections.
    """

    from pydatalab.models.collections import Collection

    collections: List[Collection] = Field([])
    """Inlined info for the collections associated with this item."""

    @root_validator
    def add_missing_collection_relationships(cls, values):
        from pydatalab.models.relationships import TypedRelationship

        if values.get("collections") is not None:
            new_ids = {coll.immutable_id for coll in values["collections"]}
            existing_collection_relationship_ids = set()
            if values.get("relationships") is not None:
                existing_collection_relationship_ids = {
                    relationship.immutable_id
                    for relationship in values["relationships"]
                    if relationship.type == "collections"
                }
            else:
                values["relationships"] = []

            for collection in values.get("collections", []):
                if collection.immutable_id not in existing_collection_relationship_ids:
                    relationship = TypedRelationship(
                        relation=None,
                        immutable_id=collection.immutable_id,
                        type="collections",
                        description="Is a member of",
                    )
                    values["relationships"].append(relationship)

            values["relationships"] = [
                d
                for d in values.get("relationships", [])
                if d.type != "collections" or d.immutable_id in new_ids
            ]

        if len([d for d in values.get("relationships", []) if d.type == "collections"]) != len(
            values.get("collections", [])
        ):
            raise RuntimeError("Relationships and collections mismatch")

        return values


class IsDeletable(BaseModel):
    """Adds a 'private' trait for whether the item is deleted.
    This can be used to soft-delete entries in the database.
    """

    deleted: bool = Field(None)

    @root_validator(pre=True)
    def check_deleted(cls, values):
        """If `deleted` is set to anything but `True`, drop the field."""
        if "deleted" in values and values["deleted"] is not True:
            values.pop("deleted")
        return values
