from typing import Literal

from pydatalab.models.items import Item


class Equipment(Item):
    """A model for representing an experimental sample."""

    type: Literal["equipment"] = "equipment"

    serial_numbers: str | None = None
    """A string describing one or more serial numbers for the instrument."""

    manufacturer: str | None = None
    """The manufacturer of this piece of equipment"""

    location: str | None = None
    """Place where the equipment is located"""

    contact: str | None = None
    """Contact information for equipment (e.g., email address or phone number)."""
