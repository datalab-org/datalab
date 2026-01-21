from typing import Any

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.blocks import DataBlockResponse
from pydatalab.models.people import Group, Person
from pydatalab.models.utils import Constituent, InlineSubstance, PyObjectId


class HasOwner(BaseModel):
    creator_ids: list[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: list[Person] | None = Field(None)
    """Inlined info for the people associated with this item."""

    group_ids: list[PyObjectId] = Field([])
    """The database IDs of the group(s) that have read-access to this item."""

    groups: list[Group] | None = Field(None)
    """Inlined info for the groups with access to this item."""


class HasRevisionControl(BaseModel):
    revision: int = 1
    """The revision number of the entry."""

    revisions: dict[int, Any] | None = None
    """An optional mapping from old revision numbers to the model state at that revision."""

    version: int = 1
    """The version number used by the version control system for tracking snapshots."""


class HasBlocks(BaseModel):
    blocks_obj: dict[str, DataBlockResponse] = Field({})
    """A mapping from block ID to block data."""

    display_order: list[str] = Field([])
    """The order in which to display block data in the UI."""


class IsCollectable(BaseModel):
    """Trait mixin for models that can be
    added to collections.
    """

    from pydatalab.models.collections import Collection

    collections: list[Collection] = Field([])
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


class HasSynthesisInfo(BaseModel):
    """Trait mixin for models that have synthesis information."""

    synthesis_constituents: list[Constituent] = Field([])
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: str | None = None
    """Free-text details of the procedure applied to synthesise the sample"""

    @root_validator
    def add_missing_synthesis_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        constituents_set = set()
        if values.get("synthesis_constituents") is not None:
            existing_parent_relationship_ids = set()
            if values.get("relationships") is not None:
                existing_parent_relationship_ids = {
                    relationship.refcode or relationship.item_id
                    for relationship in values["relationships"]
                    if relationship.relation == RelationshipType.PARENT
                }
            else:
                values["relationships"] = []

            for constituent in values.get("synthesis_constituents", []):
                # If this is an inline relationship, just skip it
                if isinstance(constituent.item, InlineSubstance):
                    continue

                constituent_id = constituent.item.refcode or constituent.item.item_id

                if constituent_id not in existing_parent_relationship_ids:
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARENT,
                        refcode=constituent.item.refcode,
                        item_id=constituent.item.item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)

                # Accumulate all constituent IDs in a set to filter those that have been deleted
                constituents_set.add(constituent_id)

        # Finally, filter out any parent relationships with item that were removed
        # from the synthesis constituents
        values["relationships"] = [
            rel
            for rel in values["relationships"]
            if not (
                (rel.refcode or rel.item_id) not in constituents_set
                and rel.relation == RelationshipType.PARENT
                and rel.type in ("samples", "starting_materials")
            )
        ]

        return values


class HasChemInfo:
    smile: str | None = Field(None)
    """A SMILES string representation of the chemical structure associated with this sample."""
    inchi: str | None = Field(None)
    """An InChI string representation of the chemical structure associated with this sample."""
    inchi_key: str | None = Field(None)
    """An InChI key representation of the chemical structure associated with this sample."""
    """A unique key derived from the InChI string."""
    chemform: str | None = Field(None)
