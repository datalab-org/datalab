from enum import Enum
from typing import Any, ClassVar, Literal

from pydantic import (
    Field,
    field_validator,
    model_validator,
)

from pydatalab.models.items import Item
from pydatalab.models.traits.ui_hints import HasUIHints, UIFieldConfig
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


class Cell(Item, HasUIHints):
    """A model for representing electrochemical cells."""

    type: Literal["cells"] = "cells"

    cell_format: CellFormat | None = Field(
        None,
        title="Cell Format",
        description="The form factor of the cell, e.g., coin, pouch, in situ or otherwise.",
    )

    cell_format_description: str | None = Field(
        None,
        description="Additional human-readable description of the cell form factor, e.g., 18650, AMPIX, CAMPIX",
    )

    cell_preparation_description: str | None = Field(
        None, description="Description of how the cell was prepared."
    )

    characteristic_mass: float | None = Field(
        None,
        title="Active mass (mg)",
        description="The characteristic mass of the cell in milligrams. Can be used to normalize capacities.",
    )

    characteristic_chemical_formula: str | None = Field(
        None,
        title="Active formula",
        description="The chemical formula of the active material. Can be used to calculated molar mass in g/mol for normalizing capacities.",
    )

    characteristic_molar_mass: float | None = Field(
        None,
        title="Molar mass",
        description="The molar mass of the active material, in g/mol. Will be inferred from the chemical formula, or can be supplied if it cannot be supplied",
    )

    positive_electrode: list[CellComponent] = Field(default_factory=list)
    negative_electrode: list[CellComponent] = Field(default_factory=list)
    electrolyte: list[CellComponent] = Field(default_factory=list)

    active_ion_charge: float = 1

    active_ion: str | None = Field(None, description="The active ion species.")

    ui_layout: ClassVar[list[list[str]]] = [
        ["name", "date"],
        ["refcode", "creators", "collections"],
        ["cell_format", "cell_format_description"],
        ["characteristic_mass", "characteristic_chemical_formula", "characteristic_molar_mass"],
        ["description"],
        ["table_of_contents"],
        ["cell_preparation_information"],
    ]

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {
        "name": UIFieldConfig(component="input", width="col-sm-8 pr-2 col-6"),
        "item_id": UIFieldConfig(
            component="FormattedItemName", width="col-sm-4 pr-2 col-6", hidden=True
        ),
        "date": UIFieldConfig(component="input", width="col-sm-4 col-6"),
        "refcode": UIFieldConfig(
            component="FormattedRefcode", width="col-md-3 col-sm-4 col-6", readonly=True
        ),
        "creators": UIFieldConfig(
            component="ToggleableCreatorsFormGroup",
            width="col-md-3 col-sm-3 col-6 pb-3",
            has_builtin_label=True,
        ),
        "collections": UIFieldConfig(
            component="ToggleableCollectionFormGroup",
            width="col-md-6 col-sm-7 pr-2",
            has_builtin_label=True,
        ),
        "cell_format": UIFieldConfig(component="select", width="col-sm-4"),
        "cell_format_description": UIFieldConfig(component="input", width="col-sm-8"),
        "characteristic_mass": UIFieldConfig(component="input", width="col-sm-4 pr-2 col-6"),
        "characteristic_chemical_formula": UIFieldConfig(
            component="ChemFormulaInput", width="col-sm-4 pr-2 col-6"
        ),
        "characteristic_molar_mass": UIFieldConfig(component="input", width="col-sm-4 col-6"),
        "active_ion": UIFieldConfig(component="input", width="col-sm-6", hidden=True),
        "active_ion_charge": UIFieldConfig(component="input", width="col-sm-6", hidden=True),
        "positive_electrode": UIFieldConfig(
            component="ConstituentsList", width="col-12", hidden=True
        ),
        "negative_electrode": UIFieldConfig(
            component="ConstituentsList", width="col-12", hidden=True
        ),
        "electrolyte": UIFieldConfig(component="ConstituentsList", width="col-12", hidden=True),
        "cell_preparation_description": UIFieldConfig(
            component="TinyMceInline", width="col-12", hidden=True
        ),
        "description": UIFieldConfig(component="TinyMceInline", width="col-12"),
        "table_of_contents": UIFieldConfig(
            component="TableOfContents", width="col-12", hide_label=True
        ),
        "cell_preparation_information": UIFieldConfig(
            component="CellPreparationInformation", width="col-12", hide_label=True
        ),
    }

    ui_virtual_fields: ClassVar[dict[str, dict[str, Any]]] = {
        "table_of_contents": {
            "title": "Table of Contents",
        },
        "cell_preparation_information": {
            "title": "Cell Preparation Information",
        },
    }

    ui_table_of_contents: ClassVar[list[dict[str, str]]] = [
        {"title": "Sample Information", "targetID": "cells-information"},
        {"title": "Table of Contents", "targetID": "table-of-contents"},
        {"title": "Cell Construction", "targetID": "cell-preparation-information"},
    ]

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
