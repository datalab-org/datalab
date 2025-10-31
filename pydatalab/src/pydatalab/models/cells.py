from enum import Enum

from pydantic import Field, root_validator, validator

from pydatalab.models.entries import EntryReference
from pydatalab.models.items import Item
from pydatalab.models.utils import CellStatus, Constituent

# from pydatalab.logger import LOGGER


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

    cell_format: CellFormat | None
    """The form factor of the cell, e.g., coin, pouch, in situ or otherwise."""

    cell_format_description: str | None
    """Additional human-readable description of the cell form factor, e.g., 18650, AMPIX, CAMPIX"""

    cell_preparation_description: str | None

    characteristic_mass: float | None
    """The characteristic mass of the cell in milligrams. Can be used to normalize capacities."""

    characteristic_chemical_formula: str | None
    """The chemical formula of the active material. Can be used to calculated molar mass in g/mol for normalizing capacities."""

    characteristic_molar_mass: float | None
    """The molar mass of the active material, in g/mol. Will be inferred from the chemical formula, or can be supplied if it cannot be supplied"""

    positive_electrode: list[CellComponent] = []

    negative_electrode: list[CellComponent] = []

    electrolyte: list[CellComponent] = []

    active_ion_charge: float = 1

    status: CellStatus = Field(default=CellStatus.ACTIVE)
    """The status of the cells, indicating its current state."""

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
                relationship.refcode or relationship.item_id
                for relationship in values["relationships"]
                if relationship.relation == RelationshipType.PARTHOOD
            }
        else:
            values["relationships"] = []

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in values.get(component, []):
                if (
                    isinstance(constituent.item, EntryReference)
                    and (constituent.item.refcode or constituent.item.item_id)
                    not in existing_parthood_relationship_ids
                ):
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARTHOOD,
                        refcode=constituent.item.refcode,
                        item_id=constituent.item.item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)

        return values
