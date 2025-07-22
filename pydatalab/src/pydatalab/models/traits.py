from typing import TYPE_CHECKING, Any

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from pydatalab.models.people import Person
from pydatalab.models.utils import Constituent, PyObjectId

if TYPE_CHECKING:
    from pydatalab.models.collections import Collection


class HasOwner(BaseModel):
    creator_ids: list[PyObjectId] = Field(default_factory=list)
    """The database IDs of the user(s) who created the item."""

    creators: list[Person] | None = Field(None)
    """Inlined info for the people associated with this item."""


class HasRevisionControl(BaseModel):
    revision: int = 1
    """The revision number of the entry."""

    revisions: dict[int, Any] | None = None
    """An optional mapping from old revision numbers to the model state at that revision."""


class HasBlocks(BaseModel):
    blocks_obj: dict[str, Any] = Field(default_factory=dict)
    """A mapping from block ID to block data."""

    display_order: list[str] = Field(default_factory=list)
    """The order in which to display block data in the UI."""


class IsCollectable(BaseModel):
    """Trait mixin for models that can be
    added to collections.
    """

    collections: list["Collection"] = Field(default_factory=list)
    """Inlined info for the collections associated with this item."""

    @model_validator(mode="before")
    @classmethod
    def add_missing_collection_relationships(cls, values):
        if values.get("collections") is not None:
            collection_ids_set = set()

            for coll in values["collections"]:
                if isinstance(coll, dict):
                    immutable_id = coll.get("immutable_id")
                else:
                    immutable_id = getattr(coll, "immutable_id", None)
                if immutable_id:
                    collection_ids_set.add(immutable_id)

            existing_collection_relationship_ids = set()
            if values.get("relationships") is not None:
                for relationship in values["relationships"]:
                    if isinstance(relationship, dict):
                        rel_type = relationship.get("type")
                        if rel_type == "collections":
                            immutable_id = relationship.get("immutable_id")
                            if immutable_id:
                                existing_collection_relationship_ids.add(immutable_id)
                    else:
                        rel_type = getattr(relationship, "type", None)
                        if rel_type == "collections":
                            immutable_id = getattr(relationship, "immutable_id", None)
                            if immutable_id:
                                existing_collection_relationship_ids.add(immutable_id)
            else:
                values["relationships"] = []

            for collection_id in collection_ids_set:
                if collection_id not in existing_collection_relationship_ids:
                    relationship_dict = {
                        "relation": None,
                        "immutable_id": collection_id,
                        "type": "collections",
                        "description": "Is a member of",
                    }
                    values["relationships"].append(relationship_dict)

            values["relationships"] = [
                rel
                for rel in values["relationships"]
                if not (
                    (
                        isinstance(rel, dict)
                        and rel.get("type") == "collections"
                        and rel.get("immutable_id") not in collection_ids_set
                    )
                    or (
                        hasattr(rel, "type")
                        and rel.type == "collections"
                        and getattr(rel, "immutable_id", None) not in collection_ids_set
                    )
                )
            ]

        return values


class HasSynthesisInfo(BaseModel):
    """Trait mixin for models that have synthesis information."""

    synthesis_constituents: list[Constituent] = Field(default_factory=list)
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: str | None = None
    """Free-text details of the procedure applied to synthesise the sample"""

    @model_validator(mode="before")
    @classmethod
    def add_missing_synthesis_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType

        if not isinstance(values, dict):
            return values

        if values.get("synthesis_constituents") is not None:
            existing_relationships = values.get("relationships", [])
            existing_parent_relationship_ids = set()

            if existing_relationships:
                for relationship in existing_relationships:
                    if isinstance(relationship, dict):
                        relation = relationship.get("relation")
                        if relation == RelationshipType.PARENT or relation == "parent":
                            ref_id = relationship.get("refcode") or relationship.get("item_id")
                            if ref_id:
                                existing_parent_relationship_ids.add(ref_id)
                    else:
                        if (
                            hasattr(relationship, "relation")
                            and relationship.relation == RelationshipType.PARENT
                        ):
                            ref_id = getattr(relationship, "refcode", None) or getattr(
                                relationship, "item_id", None
                            )
                            if ref_id:
                                existing_parent_relationship_ids.add(ref_id)

            if "relationships" not in values:
                values["relationships"] = []

            current_constituents_set = set()
            for constituent in values.get("synthesis_constituents", []):
                if isinstance(constituent, dict):
                    item_data = constituent.get("item")
                else:
                    item_data = getattr(constituent, "item", None)

                if item_data is None:
                    continue

                if isinstance(item_data, dict):
                    item_id = item_data.get("item_id")
                    refcode = item_data.get("refcode")
                    item_type = item_data.get("type")
                else:
                    item_id = getattr(item_data, "item_id", None)
                    refcode = getattr(item_data, "refcode", None)
                    item_type = getattr(item_data, "type", None)

                if not item_id and not refcode:
                    continue

                constituent_id = refcode or item_id
                current_constituents_set.add(constituent_id)

                if constituent_id and constituent_id not in existing_parent_relationship_ids:
                    relationship_dict = {
                        "relation": RelationshipType.PARENT.value,
                        "refcode": refcode,
                        "item_id": item_id,
                        "type": item_type,
                        "description": "Is a constituent of",
                    }
                    values["relationships"].append(relationship_dict)

            if "relationships" in values:
                filtered_relationships = []
                for rel in values["relationships"]:
                    if isinstance(rel, dict):
                        rel_id = rel.get("refcode") or rel.get("item_id")
                        relation = rel.get("relation")
                        rel_type = rel.get("type")
                        description = rel.get("description")
                    else:
                        rel_id = getattr(rel, "refcode", None) or getattr(rel, "item_id", None)
                        relation = getattr(rel, "relation", None)
                        rel_type = getattr(rel, "type", None)
                        description = getattr(rel, "description", None)

                    is_constituent_relationship = (
                        relation == RelationshipType.PARENT
                        and rel_type in ("samples", "starting_materials")
                        and description == "Is a constituent of"
                    )

                    if not is_constituent_relationship or rel_id in current_constituents_set:
                        filtered_relationships.append(rel)

                values["relationships"] = filtered_relationships

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
