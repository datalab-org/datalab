from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSubstanceInfo, HasSynthesisInfo
from pydatalab.models.utils import IsoformatDateTime, StartingMaterialsStatus


class StartingMaterial(Item, HasSynthesisInfo, HasSubstanceInfo):
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

    chemical_purity: str | None = Field(None, alias="Chemical purity")
    """The chemical purity of this container with regards to the defined substance."""

    full_percent: str | None = Field(None, alias="Full %")
    """The amount of the defined substance remaining in the container, expressed as a percentage."""

    name: str | None = Field(None, alias="Container Name")
    """The name of the substance in the container."""

    size: str | None = Field(None, alias="Container Size")
    """The total size of the container, in units of `size_unit`."""

    size_unit: str | None = Field(None, alias="Unit")
    """Units for the 'size' field."""

    supplier: str | None = Field(None, alias="Supplier")
    """Supplier or manufacturer of the chemical."""

    location: str | None = Field(None, alias="Location")
    """The place where the container is located."""

    comment: str | None = Field(None, alias="Comments")
    """Any additional comments or notes about the container."""

    status: StartingMaterialsStatus = Field(default=StartingMaterialsStatus.AVAILABLE)
    """The status of the starting materials, indicating its current state."""
