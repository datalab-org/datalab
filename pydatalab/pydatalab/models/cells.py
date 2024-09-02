from enum import Enum
from typing import List, Optional

from pydantic import Field, root_validator, validator

from pydatalab.models.entries import EntryReference
from pydatalab.models.items import Item
from pydatalab.models.utils import Constituent


class CellComponent(Constituent): ...


class CellFormat(str, Enum):
    coin = "coin"
    pouch = "pouch"
    in_situ_xrd = "in situ (XRD)"
    in_situ_nmr = "in situ (NMR)"
    in_situ_squid = "in situ (SQUID)"
    in_situ_optical = "in situ (optical)"
    swagelok = "swagelok"
    cylindrical = "cylindrical"
    other = "other"


class Cell(Item):
    """A model for representing electrochemical cells."""

    type: str = Field("cells", const="cells", pattern="^cells$")

    cell_format: Optional[CellFormat] = Field(
        None,
        description="The form factor of the cell, e.g., coin, pouch, in situ or otherwise.",
    )

    cell_format_description: Optional[str] = Field(
        None,
        description="Additional human-readable description of the cell form factor, e.g., 18650, AMPIX, CAMPIX",
    )

    cell_preparation_description: Optional[str] = Field(None)

    characteristic_mass: Optional[float] = Field(
        None,
        description="The characteristic mass of the cell in milligrams. Can be used to normalize capacities.",
    )

    characteristic_chemical_formula: Optional[str] = Field(
        None,
        description="The chemical formula of the active material. Can be used to calculated molar mass in g/mol for normalizing capacities.",
    )

    characteristic_molar_mass: Optional[float] = Field(
        None,
        description="The molar mass of the active material, in g/mol. Will be inferred from the chemical formula, or can be supplied if it cannot be supplied",
    )

    positive_electrode: List[CellComponent] = Field([])

    negative_electrode: List[CellComponent] = Field([])

    electrolyte: List[CellComponent] = Field([])

    active_ion_charge: float = Field(1)

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("characteristic_molar_mass", always=True, pre=True)
    def set_molar_mass(cls, v, values):
        from periodictable import formula

        if not v:
            chemical_formula = values.get("characteristic_chemical_formula")

            if chemical_formula:
                try:
                    return formula(chemical_formula).mass
                except Exception:
                    return None

        return v

    @root_validator
    def add_missing_electrode_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        existing_parthood_relationship_ids = set()
        if values.get("relationships") is not None:
            existing_parthood_relationship_ids = {
                relationship.item_id
                for relationship in values["relationships"]
                if relationship.relation == RelationshipType.PARTHOOD
            }
        else:
            values["relationships"] = []

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in values.get(component, []):
                if (
                    isinstance(constituent.item, EntryReference)
                    and constituent.item.item_id not in existing_parthood_relationship_ids
                ):
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARTHOOD,
                        item_id=constituent.item.item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)

        return values
