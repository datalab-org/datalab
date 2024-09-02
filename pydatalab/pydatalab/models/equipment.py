from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item


class Equipment(Item):
    """A model for representing an experimental sample."""

    type: str = Field("equipment", const="equipment", pattern="^equipment$")

    serial_numbers: Optional[str] = None
    """A string describing one or more serial numbers for the instrument."""

    manufacturer: Optional[str] = None
    """The manufacturer of this piece of equipment"""

    location: Optional[str] = None
    """Place where the equipment is located"""

    contact: Optional[str] = None
    """Contact information for equipment (e.g., email address or phone number)."""
