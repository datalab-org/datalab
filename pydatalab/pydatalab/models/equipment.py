from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item


class Equipment(Item):
    """A model for representing an experimental sample."""

    type: str = Field("equipment", const="equipment", pattern="^equipment$")

    serial_numbers: Optional[str]
    """A string describing one or more serial numbers for the instrument."""

    manufacturer: Optional[str]
    """The manufacturer of this piece of equipment"""

    location: Optional[str]
    """Place where the equipment is located"""
