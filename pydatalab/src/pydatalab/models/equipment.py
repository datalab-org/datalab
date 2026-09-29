# This file was edited with the assistance of an AI model and requires human review from the contributor.
from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.utils import (
    EquipmentStatus,
)


class Equipment(Item):
    """A model for representing a piece of equipment.

    Equipment represents an instrument or apparatus in the lab, which can be linked to
    the items measured on it.
    """

    type: Literal["equipment"] = "equipment"

    serial_numbers: str | None = None
    """A string describing one or more serial numbers for the instrument."""

    manufacturer: str | None = None
    """The manufacturer of this piece of equipment"""

    contact: str | None = None
    """Contact information for equipment (e.g., email address or phone number)."""

    status: EquipmentStatus = Field(
        default=EquipmentStatus.WORKING,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """The status of the equipment, indicating its current state."""
