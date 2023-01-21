from typing import List, Optional

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.utils import JSON_ENCODERS


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemform: Optional[str] = Field(
        description="A string representation of the chemical formula associated with this sample."
    )

    synthesis_constituents: List[dict] = Field(
        [], description="Dictionary giving amount and details of consituent items"
    )

    synthesis_description: Optional[str] = Field(description="Details of the sample synthesis")

    class Config:
        allow_arbitrary_types = True
        json_encoders = JSON_ENCODERS
