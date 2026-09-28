from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSubstanceInfo, HasSynthesisInfo
from pydatalab.models.utils import IsoformatDateTime, StartingMaterialsStatus


class StartingMaterial(Item, HasSynthesisInfo, HasSubstanceInfo):
    """A model for representing a starting material, i.e., a chemical or precursor held
    in the lab's inventory, from which samples are made.

    The model mixes container-level and substance-level information and can be used to
    represent either depending on preference.
    """

    type: Literal["starting_materials"] = "starting_materials"

    barcode: str | None = Field(
        None, alias="Barcode", json_schema_extra={"datalab_include_field_in_summary": True}
    )
    """A unique barcode provided by an external source, e.g., cheminventory."""

    date: IsoformatDateTime | None = Field(
        None, alias="Date Acquired", json_schema_extra={"datalab_include_field_in_summary": True}
    )
    """The date the item was acquired"""

    date_opened: IsoformatDateTime | None = Field(
        None, alias="Date opened", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """The date the item was opened"""

    chemical_purity: str | None = Field(
        None, alias="Chemical purity", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """The chemical purity of this container with regards to the defined substance."""

    full_percent: str | None = Field(
        None, alias="Full %", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """The amount of the defined substance remaining in the container, expressed as a percentage."""

    name: str | None = Field(
        None, alias="Container Name", json_schema_extra={"datalab_include_field_in_summary": True}
    )
    """The name of the substance in the container."""

    size: str | None = Field(
        None, alias="Container Size", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """The total size of the container, in units of `size_unit`."""

    size_unit: str | None = Field(
        None, alias="Unit", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """Units for the 'size' field."""

    supplier: str | None = Field(
        None, alias="Supplier", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """Supplier or manufacturer of the chemical."""

    comment: str | None = Field(
        None, alias="Comments", json_schema_extra={"datalab_include_field_in_summary": False}
    )
    """Any additional comments or notes about the container."""

    status: StartingMaterialsStatus = Field(
        default=StartingMaterialsStatus.AVAILABLE,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """The status of the starting materials, indicating its current state."""
