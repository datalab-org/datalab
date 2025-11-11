from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.utils import EquipmentStatus


class Equipment(Item):
    """A model for representing an experimental sample."""

    type: Literal["equipment"] = "equipment"

    serial_numbers: str | None = Field(
        None, description="A string describing one or more serial numbers for the instrument."
    )

    manufacturer: str | None = Field(
        None, description="The manufacturer of this piece of equipment"
    )

    location: str | None = Field(None, description="Place where the equipment is located")

    contact: str | None = Field(
        None, description="Contact information for equipment (e.g., email address or phone number)."
    )

    status: EquipmentStatus = Field(
        default=EquipmentStatus.WORKING,
        description="The status of the equipment, indicating its current state.",
    )
