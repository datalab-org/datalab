import datetime
from typing import Optional

from pydantic import Field, validator

from pydatalab.models.items import Item


class StartingMaterial(Item):
    """A model for representing an experimental sample."""

    type: str = Field(
        "starting_materials", const="starting_materials", pattern="^starting_materials$"
    )

    barcode: Optional[str] = Field(
        alias="Barcode", description="A unique barcode from ChemInventory"
    )

    date_acquired: Optional[datetime.datetime] = Field(
        alias="Date Acquired", description="The date the item was acquired"
    )

    date_opened: Optional[datetime.datetime] = Field(
        alias="Date opened", description="The date the container was opened"
    )

    CAS: Optional[str] = Field(alias="Substance CAS", description="CAS Registry Number")

    chemical_purity: Optional[str] = Field(alias="Chemical purity")

    full_percent: Optional[str] = Field(alias="Full %")

    name: str = Field(alias="Container Name", description="name of the chemical")

    size: Optional[str] = Field(
        alias="Container Size", description="size of the container (see 'size_unit' for the units)"
    )

    size_unit: Optional[str] = Field(alias="Unit", description="units for the 'size' field.")

    chemform: Optional[str] = Field(
        alias="Molecular Formula",
        description="A string representation of the chemical formula associated with this sample.",
    )

    molar_mass: Optional[float] = Field(
        alias="Molecular Weight", description="Mass per formula unit, in g/mol"
    )

    smiles_representation: Optional[str] = Field(
        alias="SMILES", description="Chemical structure in SMILES notation"
    )

    supplier: Optional[str] = Field(alias="Supplier", description="Manufacturer of the chemical")

    location: Optional[str] = Field(
        alias="Location", description="Location where chemical is stored"
    )

    comment: Optional[str] = Field(alias="Comments")

    @validator("date_acquired", "date_opened", pre=True)
    def cast_to_date(cls, v):
        if isinstance(v, str):
            if v in ["0", " "]:
                return None
        return v

    class Config:
        extras = "ignore"
        allow_population_by_field_name = True
