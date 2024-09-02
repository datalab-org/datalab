from typing import Optional

from pydantic import Field, validator

from pydatalab.models.items import Item
from pydatalab.models.utils import IsoformatDateTime


class StartingMaterial(Item):
    """A model for representing an experimental sample."""

    type: str = Field(
        "starting_materials", const="starting_materials", pattern="^starting_materials$"
    )

    barcode: Optional[str] = Field(
        None, alias="Barcode", description="A unique barcode from ChemInventory"
    )

    date: Optional[IsoformatDateTime] = Field(
        None, alias="Date Acquired", description="The date the item was acquired"
    )

    date_opened: Optional[IsoformatDateTime] = Field(
        None, alias="Date opened", description="The date the container was opened"
    )

    CAS: Optional[str] = Field(None, alias="Substance CAS", description="CAS Registry Number")

    chemical_purity: Optional[str] = Field(None, alias="Chemical purity")

    full_percent: Optional[str] = Field(None, alias="Full %")

    GHS_codes: Optional[str] = Field(
        None,
        alias="GHS H-codes",
        description="A string describing any GHS hazard codes associated with this item. See https://pubchem.ncbi.nlm.nih.gov/ghs/ for code definitions.",
        examples=["H224", "H303, H316, H319"],
    )

    name: Optional[str] = Field(None, alias="Container Name", description="name of the chemical")

    size: Optional[str] = Field(
        None,
        alias="Container Size",
        description="size of the container (see 'size_unit' for the units)",
    )

    size_unit: Optional[str] = Field(None, alias="Unit", description="units for the 'size' field.")

    chemform: Optional[str] = Field(
        None,
        alias="Molecular Formula",
        description="A string representation of the chemical formula associated with this sample.",
    )

    molar_mass: Optional[float] = Field(
        None, alias="Molecular Weight", description="Mass per formula unit, in g/mol"
    )

    smiles_representation: Optional[str] = Field(
        None, alias="SMILES", description="Chemical structure in SMILES notation"
    )

    supplier: Optional[str] = Field(
        None, alias="Supplier", description="Manufacturer of the chemical"
    )

    location: Optional[str] = Field(
        None, alias="Location", description="Location where chemical is stored"
    )

    comment: Optional[str] = Field(None, alias="Comments")

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("molar_mass")
    def add_molar_mass(cls, v, values):
        from periodictable import formula

        if v is None and values.get("chemform"):
            return formula(values.get("chemform")).mass

        return v
