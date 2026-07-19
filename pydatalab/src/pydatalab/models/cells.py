from enum import Enum
from typing import Literal

from pydantic import (
    Field,
    field_validator,
    model_validator,
)

from pydatalab.models.entries import EntryReference
from pydatalab.models.items import Item
from pydatalab.models.utils import CellStatus, Constituent

# Conversion factor from nominal_capacity_unit to the base unit (mAh). Single source of
# truth: used by `set_nominal_capacity`, so any downstream consumer normalizes
# consistently regardless of which unit is currently selected on a given item.
NOMINAL_CAPACITY_TO_MAH = {"mAh": 1, "Ah": 1e3}


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
    active_ion: str | None = None
    """The active ion species."""
    active_ion_charge: float = 1
    status: CellStatus = Field(default=CellStatus.ACTIVE)
    """The status of the cells, indicating its current state."""

    theoretical_capacity: float | None = None
    """The theoretical specific capacity of the active material, in mAh/g."""

    nominal_capacity_unit: Literal["mAh", "Ah"] = "mAh"
    """The unit that `nominal_capacity` is given in."""

    nominal_capacity: float | None = None
    """The nominal capacity of the cell, computed as
    `theoretical_capacity * characteristic_mass`. See `set_nominal_capacity`."""

    nominal_capacity_mah: float | None = None
    """`nominal_capacity` normalized to mAh, regardless of the unit currently selected
    on this item (`nominal_capacity_unit`). Read-only/derived: always recomputed on
    save (see `set_nominal_capacity`). Prefer this field over `nominal_capacity`
    whenever comparing or aggregating across cells, since `nominal_capacity_unit` can
    differ from item to item."""

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

    @model_validator(mode="after")
    def set_nominal_capacity(self):
        if self.theoretical_capacity is None or self.characteristic_mass is None:
            self.nominal_capacity_mah = None
            return self

        # theoretical_capacity is in mAh/g; characteristic_mass is in mg (divide by
        # 1000 to get grams).
        nominal_capacity_mah = self.theoretical_capacity * self.characteristic_mass / 1000

        self.nominal_capacity_mah = nominal_capacity_mah
        self.nominal_capacity = (
            nominal_capacity_mah / NOMINAL_CAPACITY_TO_MAH[self.nominal_capacity_unit]
        )
        return self

    @model_validator(mode="after")
    def add_missing_electrode_relationships(self):
        """Add any missing cell component constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        # Index by refcode *and* item_id so a stored relationship carrying an
        # item_id still matches a refcode-enriched constituent (and vice-versa).
        existing_parthood_relationships = {
            identifier: relationship
            for relationship in self.relationships
            if relationship.relation == RelationshipType.PARTHOOD
            for identifier in (relationship.refcode, relationship.item_id)
            if identifier
        }

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in getattr(self, component):
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
                    self.relationships.append(relationship)
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

        return self
