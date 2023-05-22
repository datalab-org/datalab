import abc
from typing import Any, Dict, List, Optional

from pydantic import Field, root_validator, validator

from pydatalab.models.collections import CollectionReference
from pydatalab.models.entries import Entry
from pydatalab.models.files import File
from pydatalab.models.traits import HasOwner, HasRevisionControl
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
    Refcode,
)


class Item(Entry, HasOwner, HasRevisionControl, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    refcode: Refcode = None  # type: ignore
    """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`)
    and a locally unique string, ideally created with some consistent scheme.
    """

    item_id: HumanReadableIdentifier
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

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

    files: Optional[List[File]]
    """Any files attached to this sample."""

    file_ObjectIds: List[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""

    @validator("refcode", pre=True, always=True)
    def refcode_validator(cls, v):
        """Generate a refcode if not provided; check that the refcode has the correct prefix if provided."""

        from pydatalab.config import CONFIG

        if v and not v.startswith(f"{CONFIG.IDENTIFIER_PREFIX}:"):
            raise ValueError(f"refcode missing prefix {CONFIG.IDENTIFIER_PREFIX!r}")

        return v

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
