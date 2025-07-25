from typing import Literal

from pydantic import Field, field_validator

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo
from pydatalab.models.utils import IsoformatDateTime


class StartingMaterial(Item, HasSynthesisInfo):
    """A model for representing an experimental sample, based on the connection
    with cheminventory.net, which mixes container-level and substance-level
    information.
    """

    type: Literal["starting_materials"] = "starting_materials"

    barcode: str | None = Field(None, alias="Barcode")
    """A unique barcode provided by an external source, e.g., cheminventory."""

    date: IsoformatDateTime | None = Field(None, alias="Date Acquired")
    """The date the item was acquired"""

    date_opened: IsoformatDateTime | None = Field(None, alias="Date opened")
    """The date the item was opened"""

    CAS: str | None = Field(None, alias="Substance CAS")
    """The CAS Registry Number for the substance described by this entry."""

    chemical_purity: str | None = Field(None, alias="Chemical purity")
    """The chemical purity of this container with regards to the defined substance."""

    full_percent: str | None = Field(None, alias="Full %")
    """The amount of the defined substance remaining in the container, expressed as a percentage."""

    GHS_codes: str | None = Field(None, alias="GHS H-codes", examples=["H224", "H303, H316, H319"])
    """A string describing any GHS hazard codes associated with this item."""

    name: str | None = Field(None, alias="Container Name")
    """The name of the substance in the container."""

    size: str | None = Field(None, alias="Container Size")
    """The total size of the container, in units of `size_unit`."""

    size_unit: str | None = Field(None, alias="Unit")
    """Units for the 'size' field."""

    chemform: str | None = Field(None, alias="Molecular Formula")
    """A string representation of the chemical formula associated with this sample."""

    molar_mass: float | None = Field(None, alias="Molecular Weight")
    """Mass per formula unit, in g/mol."""

    smiles_representation: str | None = Field(None, alias="SMILES")
    """A SMILES string representation of a chemical structure associated with this substance."""

    supplier: str | None = Field(None, alias="Supplier")
    """Supplier or manufacturer of the chemical."""

    location: str | None = Field(None, alias="Location")
    """The place where the container is located."""

    comment: str | None = Field(None, alias="Comments")
    """Any additional comments or notes about the container."""

    @field_validator("molar_mass", mode="before")
    @classmethod
    def add_molar_mass(cls, v, info):
        from periodictable import formula

        if v is None and hasattr(info, "data") and info.data:
            chemform = info.data.get("chemform")
            if chemform:
                try:
                    return formula(chemform).mass
                except Exception:
                    return None
        return v
