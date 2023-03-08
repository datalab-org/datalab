from typing import List, Optional

from pydantic import BaseModel, Field, root_validator, validator

from pydatalab.models.entries import EntryReference
from pydatalab.models.items import Item
from pydatalab.models.utils import ItemType


class Constituent(BaseModel):
    """A constituent of a sample."""

    item: EntryReference = Field(...)
    """A reference to item (sample or starting material) entry for the constituent substance."""

    quantity: Optional[float] = Field(..., ge=0)
    """The amount of the constituent material used to create the sample."""

    unit: str = Field("g")
    """The unit symbol for the value provided in `quantity`, default is mass
    in grams (g) but could also refer to volumes (mL, L, etc.) or moles (mol).
    """

    @validator("item")
    def check_itemhood(cls, v):
        """Check that the reference within the constituent is to an item type."""
        if "type" in (v.value for v in ItemType):
            raise ValueError(f"`type` must be one of {ItemType!r}")

        return v


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemform: Optional[str] = Field(example=["Na3P", "LiNiO2@C"])
    """A string representation of the chemical formula or composition associated with this sample."""

    synthesis_constituents: List[Constituent] = Field([])
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: Optional[str]
    """Free-text details of the procedure applied to synthesise the sample"""

    @root_validator
    def add_missing_synthesis_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        constituents_set = set()
        if values.get("synthesis_constituents") is not None:

            existing_parent_relationship_ids = set()
            if values.get("relationships") is not None:
                existing_parent_relationship_ids = set(
                    relationship.item_id or relationship.refcode
                    for relationship in values["relationships"]
                    if relationship.relation == RelationshipType.PARENT
                )
            else:
                values["relationships"] = []

            for constituent in values.get("synthesis_constituents", []):
                if (
                    constituent.item.item_id not in existing_parent_relationship_ids
                    and constituent.item.refcode not in existing_parent_relationship_ids
                ):
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARENT,
                        item_id=constituent.item.item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)

                # Accumulate all constituent IDs in a set to filter those that have been deleted
                constituents_set.add(constituent.item.item_id)

        # Finally, filter out any parent relationships with item that were removed
        # from the synthesis constituents
        values["relationships"] = [
            rel
            for rel in values["relationships"]
            if not (
                rel.item_id not in constituents_set
                and rel.relation == RelationshipType.PARENT
                and rel.type in ("samples", "starting_materials")
            )
        ]

        return values
