import abc
from typing import Any, Dict, List, Optional

from pydantic import Field, root_validator

from pydatalab.models.collections import CollectionReference
from pydatalab.models.entries import Entry
from pydatalab.models.people import Person
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
)


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    item_id: HumanReadableIdentifier
    """A unique, human-readable identifier for the entry."""

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""

    collections: List[CollectionReference] = Field([])
    """Inlined info for the collections associated with this item."""

    description: Optional[str]
    """A description of the item, either in plain-text or a markup language."""

    date: Optional[IsoformatDateTime]
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: Optional[str]
    """An optional human-readable/usable name for the entry."""

    blocks_obj: Dict[str, Any] = Field({})
    """A mapping from block ID to block data."""

    display_order: List[str] = Field([])
    """The order in which to display block data in the UI."""

    files: Optional[List[str]]
    """Any files attached to this sample."""

    file_ObjectIds: List[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""

    @root_validator
    def add_missing_collection_relationships(cls, values):
        from pydatalab.models.relationships import TypedRelationship

        if values.get("collections") is not None:

            existing_parent_relationship_ids = set()
            collections_set = set()
            if values.get("relationships") is not None:
                existing_parent_relationship_ids = set(
                    relationship.immutable_id
                    for relationship in values["relationships"]
                    if relationship.type == "collections"
                )
            else:
                values["relationships"] = []

            for collection in values.get("collections", []):
                if collection.immutable_id not in existing_parent_relationship_ids:
                    relationship = TypedRelationship(
                        relation=None,
                        immutable_id=collection.immutable_id,
                        type="collections",
                        description="Is a member of",
                    )
                    values["relationships"].append(relationship)

                # Accumulate all constituent IDs in a set to filter those that have been deleted
                collections_set.add(collection.immutable_id)

        # Finally, filter out any parent relationships with item that were removed
        # from the synthesis constituents
        values["relationships"] = [
            rel
            for rel in values["relationships"]
            if not (rel.immutable_id not in collections_set and rel.type == "collections")
        ]

        return values
