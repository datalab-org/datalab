from typing import Any

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from pydatalab.models.blocks import DataBlockResponse
from pydatalab.models.people import Group, Person
from pydatalab.models.utils import Constituent, PyObjectId


class HasOwner(BaseModel):
    creator_ids: list[PyObjectId] = Field(
        default_factory=list, description="The database IDs of the user(s) who created the item."
    )

    creators: list[Person] | None = Field(
        None, description="Inlined info for the people associated with this item."
    )

    group_ids: list[PyObjectId] = Field(
        default_factory=list,
        description="The database IDs of the group(s) that have read-access to this item.",
    )

    groups: list[Group] | None = Field(
        None, description="Inlined info for the groups with access to this item."
    )


class HasRevisionControl(BaseModel):
    revision: int = Field(1, description="The revision number of the entry.")

    revisions: dict[int, Any] | None = Field(
        None,
        description="An optional mapping from old revision numbers to the model state at that revision.",
    )

    version: int = Field(
        1,
        description="The version number used by the version control system for tracking snapshots.",
    )


class HasBlocks(BaseModel):
    blocks_obj: dict[str, DataBlockResponse] = Field({})
    """A mapping from block ID to block data."""

    display_order: list[str] = Field([])
    """The order in which to display block data in the UI."""


class HasSynthesisInfo(BaseModel):
    """Trait mixin for models that have synthesis information."""

    synthesis_constituents: list[Constituent] = Field(
        default_factory=list,
        description="A list of references to constituent materials giving the amount and relevant inlined details of consituent items.",
    )

    synthesis_description: str | None = Field(
        None, description="Free-text details of the procedure applied to synthesise the sample"
    )

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


class HasChemInfo(BaseModel):
    smile: str | None = Field(
        None,
        description="A SMILES string representation of the chemical structure associated with this sample.",
    )

    inchi: str | None = Field(
        None,
        description="An InChI string representation of the chemical structure associated with this sample.",
    )

    inchi_key: str | None = Field(
        None,
        description="An InChI key representation of the chemical structure associated with this sample. A unique key derived from the InChI string.",
    )

    chemform: str | None = Field(None)


from pydatalab.models.traits.collectable import IsCollectable

__all__ = (
    "HasOwner",
    "HasRevisionControl",
    "HasBlocks",
    "HasSynthesisInfo",
    "HasChemInfo",
    "IsCollectable",
)
