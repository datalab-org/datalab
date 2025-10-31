from pydantic import Field, validator

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo
from pydatalab.models.utils import IsoformatDateTime, StartingMaterialsStatus


class StartingMaterial(Item, HasSynthesisInfo):
    """A model for representing an experimental sample, based on the connection
    with cheminventory.net, which mixes container-level and substance-level
    information.

    """

    type: str = Field(
        "starting_materials", const="starting_materials", pattern="^starting_materials$"
    )

    barcode: str | None = Field(
        alias="Barcode",
    )
    """A unique barcode provided by an external source, e.g., cheminventory."""

    date: IsoformatDateTime | None = Field(alias="Date Acquired")
    """The date the item was acquired"""

    date_opened: IsoformatDateTime | None = Field(alias="Date opened")
    """The date the item was opened"""

    CAS: str | None = Field(alias="Substance CAS")
    """The CAS Registry Number for the substance described by this entry."""

    chemical_purity: str | None = Field(alias="Chemical purity")
    """The chemical purity of this container with regards to the defined substance."""

    full_percent: str | None = Field(alias="Full %")
    """The amount of the defined substance remaining in the container, expressed as a percentage."""

    GHS_codes: str | None = Field(
        alias="GHS H-codes",
        examples=["H224", "H303, H316, H319"],
    )
    """A string describing any GHS hazard codes associated with this item. See https://pubchem.ncbi.nlm.nih.gov/ghs/ for code definitions."""

    name: str | None = Field(alias="Container Name")
    """The name of the substance in the container."""

    size: str | None = Field(alias="Container Size")
    """The total size of the container, in units of `size_unit`."""

    size_unit: str | None = Field(alias="Unit")
    """Units for the 'size' field."""

    chemform: str | None = Field(alias="Molecular Formula")
    """A string representation of the chemical formula associated with this sample."""

    molar_mass: float | None = Field(alias="Molecular Weight")
    """Mass per formula unit, in g/mol."""

    smiles_representation: str | None = Field(alias="SMILES")
    """A SMILES string representation of a chemical structure associated with this substance."""

    supplier: str | None = Field(alias="Supplier")
    """Supplier or manufacturer of the chemical."""

    location: str | None = Field(alias="Location")
    """The place where the container is located."""

    comment: str | None = Field(alias="Comments")
    """Any additional comments or notes about the container."""

    status: StartingMaterialsStatus = Field(default=StartingMaterialsStatus.AVAILABLE)
    """The status of the starting materials, indicating its current state."""

    @validator("molar_mass")
    def add_molar_mass(cls, v, values):
        from periodictable import formula

        if v is None and values.get("chemform"):
            try:
                return formula(values.get("chemform")).mass
            except Exception:
                return None

        return v
