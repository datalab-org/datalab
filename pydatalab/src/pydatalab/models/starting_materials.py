from typing import List, Optional

from pydantic import Field, root_validator, validator

from pydatalab.models.items import Item
from pydatalab.models.utils import Constituent, InlineSubstance, IsoformatDateTime


class StartingMaterial(Item):
    """A model for representing an experimental sample."""

    type: str = Field(
        "starting_materials", const="starting_materials", pattern="^starting_materials$"
    )

    barcode: Optional[str] = Field(
        alias="Barcode", description="A unique barcode from ChemInventory"
    )

    date: Optional[IsoformatDateTime] = Field(
        alias="Date Acquired", description="The date the item was acquired"
    )

    date_opened: Optional[IsoformatDateTime] = Field(
        alias="Date opened", description="The date the container was opened"
    )

    CAS: Optional[str] = Field(alias="Substance CAS", description="CAS Registry Number")

    chemical_purity: Optional[str] = Field(alias="Chemical purity")

    full_percent: Optional[str] = Field(alias="Full %")

    GHS_codes: Optional[str] = Field(
        alias="GHS H-codes",
        description="A string describing any GHS hazard codes associated with this item. See https://pubchem.ncbi.nlm.nih.gov/ghs/ for code definitions.",
        examples=["H224", "H303, H316, H319"],
    )

    name: Optional[str] = Field(alias="Container Name", description="name of the chemical")

    size: Optional[str] = Field(
        alias="Container Size", description="size of the container (see 'size_unit' for the units)"
    )

    size_unit: Optional[str] = Field(alias="Unit", description="units for the 'size' field.")

    chemform: Optional[str] = Field(
        alias="Molecular Formula",
        description="A string representation of the chemical formula associated with this sample.",
    )

    molar_mass: Optional[float] = Field(
        alias="Molecular Weight", description="Mass per formula unit, in g/mol"
    )

    smiles_representation: Optional[str] = Field(
        alias="SMILES", description="Chemical structure in SMILES notation"
    )

    supplier: Optional[str] = Field(alias="Supplier", description="Manufacturer of the chemical")

    location: Optional[str] = Field(
        alias="Location", description="Location where chemical is stored"
    )

    comment: Optional[str] = Field(alias="Comments")

    synthesis_constituents: List[Constituent] = Field([])
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: Optional[str]
    """Free-text details of the procedure applied to synthesise the sample"""

    @validator("molar_mass")
    def add_molar_mass(cls, v, values):
        from periodictable import formula

        if v is None and values.get("chemform"):
            return formula(values.get("chemform")).mass

        return v

    @root_validator
    def add_missing_synthesis_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        constituents_set = set()
        if values.get("synthesis_constituents") is not None:
            existing_parent_relationship_ids = set()
            if values.get("relationships") is not None:
                existing_parent_relationship_ids = {
                    relationship.item_id or relationship.refcode
                    for relationship in values["relationships"]
                    if relationship.relation == RelationshipType.PARENT
                }
            else:
                values["relationships"] = []

            for constituent in values.get("synthesis_constituents", []):
                # If this is an inline relationship, just skip it
                if isinstance(constituent.item, InlineSubstance):
                    continue
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
