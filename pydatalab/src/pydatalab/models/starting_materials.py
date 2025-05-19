from typing import Optional

from pydantic import Field, validator

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo
from pydatalab.models.utils import IsoformatDateTime


class StartingMaterial(Item, HasSynthesisInfo):
    """A model for representing an experimental sample, based on the connection
    with cheminventory.net, which mixes container-level and substance-level
    information.

    """

    type: str = Field(
        "starting_materials", const="starting_materials", pattern="^starting_materials$"
    )

    barcode: Optional[str] = Field(
        alias="Barcode",
    )
    """A unique barcode provided by an external source, e.g., cheminventory."""

    date: Optional[IsoformatDateTime] = Field(alias="Date Acquired")
    """The date the item was acquired"""

    date_opened: Optional[IsoformatDateTime] = Field(alias="Date opened")
    """The date the item was opened"""

    CAS: Optional[str] = Field(alias="Substance CAS")
    """The CAS Registry Number for the substance described by this entry."""

    chemical_purity: Optional[str] = Field(alias="Chemical purity")
    """The chemical purity of this container with regards to the defined substance."""

    full_percent: Optional[str] = Field(alias="Full %")
    """The amount of the defined substance remaining in the container, expressed as a percentage."""

    GHS_codes: Optional[str] = Field(
        alias="GHS H-codes",
        examples=["H224", "H303, H316, H319"],
    )
    """A string describing any GHS hazard codes associated with this item. See https://pubchem.ncbi.nlm.nih.gov/ghs/ for code definitions."""

    name: Optional[str] = Field(alias="Container Name")
    """The name of the substance in the container."""

    size: Optional[str] = Field(alias="Container Size")
    """The total size of the container, in units of `size_unit`."""

    size_unit: Optional[str] = Field(alias="Unit")
    """Units for the 'size' field."""

    chemform: Optional[str] = Field(alias="Molecular Formula")
    """A string representation of the chemical formula associated with this sample."""

    molar_mass: Optional[float] = Field(alias="Molecular Weight")
    """Mass per formula unit, in g/mol."""

    smiles_representation: Optional[str] = Field(alias="SMILES")
    """A SMILES string representation of a chemical structure associated with this substance."""

    supplier: Optional[str] = Field(alias="Supplier")
    """Supplier or manufacturer of the chemical."""

    location: Optional[str] = Field(alias="Location")
    """The place where the container is located."""

    comment: Optional[str] = Field(alias="Comments")
    """Any additional comments or notes about the container."""

    @validator("molar_mass")
    def add_molar_mass(cls, v, values):
        from periodictable import formula

        if v is None and values.get("chemform"):
            return formula(values.get("chemform")).mass

        return v
