from enum import Enum
from typing import Literal

from pydantic import (
    Field,
    field_validator,
    model_validator,
)

from pydatalab.models.items import Item
from pydatalab.models.utils import Constituent

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

    type: Literal["cells"] = "cells"

    cell_format: CellFormat | None = None
    """The form factor of the cell, e.g., coin, pouch, in situ or otherwise."""

    cell_format_description: str | None = None
    """Additional human-readable description of the cell form factor, e.g., 18650, AMPIX, CAMPIX"""

    cell_preparation_description: str | None = None
    """Description of how the cell was prepared."""

    characteristic_mass: float | None = None
    """The characteristic mass of the cell in milligrams. Can be used to normalize capacities."""

    characteristic_chemical_formula: str | None = None
    """The chemical formula of the active material. Can be used to calculated molar mass in g/mol for normalizing capacities."""

    characteristic_molar_mass: float | None = None
    """The molar mass of the active material, in g/mol. Will be inferred from the chemical formula, or can be supplied if it cannot be supplied"""

    positive_electrode: list[CellComponent] = Field(default_factory=list)
    negative_electrode: list[CellComponent] = Field(default_factory=list)
    electrolyte: list[CellComponent] = Field(default_factory=list)

    active_ion_charge: float = 1

    active_ion: str | None = None
    """The active ion species."""

    @field_validator("characteristic_molar_mass", mode="before")
    @classmethod
    def set_molar_mass(cls, v, info):
        from periodictable import formula

        if not v and hasattr(info, "data") and info.data:
            chemical_formula = info.data.get("characteristic_chemical_formula")
            if chemical_formula:
                try:
                    return formula(chemical_formula).mass
                except Exception:
                    return None
        return v

    @model_validator(mode="before")
    @classmethod
    def add_missing_electrode_relationships(cls, values):
        """Add any missing electrode constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType

        existing_parthood_relationship_ids = set()
        if values.get("relationships") is not None:
            for relationship in values["relationships"]:
                if isinstance(relationship, dict):
                    relation = relationship.get("relation")
                    if relation == RelationshipType.PARTHOOD or relation == "is_part_of":
                        ref_id = relationship.get("refcode") or relationship.get("item_id")
                        if ref_id:
                            existing_parthood_relationship_ids.add(ref_id)
                else:
                    if (
                        hasattr(relationship, "relation")
                        and relationship.relation == RelationshipType.PARTHOOD
                    ):
                        ref_id = getattr(relationship, "refcode", None) or getattr(
                            relationship, "item_id", None
                        )
                        if ref_id:
                            existing_parthood_relationship_ids.add(ref_id)
        else:
            values["relationships"] = []

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in values.get(component, []):
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

                    if not item_id and not refcode:
                        continue

                    constituent_id = refcode or item_id
                else:
                    item_id = getattr(item_data, "item_id", None)
                    refcode = getattr(item_data, "refcode", None)
                    item_type = getattr(item_data, "type", None)

                    if not item_id and not refcode:
                        continue

                    constituent_id = refcode or item_id

                if constituent_id and constituent_id not in existing_parthood_relationship_ids:
                    relationship_dict = {
                        "relation": RelationshipType.PARTHOOD,
                        "refcode": refcode,
                        "item_id": item_id,
                        "type": item_type,
                        "description": "Is a constituent of",
                    }
                    values["relationships"].append(relationship_dict)

        return values
