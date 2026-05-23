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
        """Add any missing cell component constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        existing_parthood_relationships = {}
        if values.get("relationships") is not None:
            # Index by refcode *and* item_id so a stored relationship carrying an
            # item_id still matches a refcode-enriched constituent (and vice-versa).
            existing_parthood_relationships = {
                identifier: relationship
                for relationship in values["relationships"]
                if relationship.relation == RelationshipType.PARTHOOD
                for identifier in (relationship.refcode, relationship.item_id)
                if identifier
            }
        else:
            values["relationships"] = []

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in values.get(component, []):
                if not isinstance(constituent.item, EntryReference):
                    continue

                refcode = constituent.item.refcode
                item_id = constituent.item.item_id

                relationship = existing_parthood_relationships.get(
                    refcode
                ) or existing_parthood_relationships.get(item_id)
                if relationship is None:
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARTHOOD,
                        refcode=refcode,
                        item_id=item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)
                else:
                    # Back-fill any identifier missing from the stored relationship
                    relationship.refcode = relationship.refcode or refcode
                    relationship.item_id = relationship.item_id or item_id

                # Register the relationship's identifiers in the index so a later
                # constituent referencing the same entry matches it rather than
                # appending a duplicate within this same validation pass.
                for identifier in (relationship.refcode, relationship.item_id):
                    if identifier:
                        existing_parthood_relationships[identifier] = relationship

        return values
