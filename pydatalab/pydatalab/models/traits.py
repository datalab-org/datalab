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

        return values
