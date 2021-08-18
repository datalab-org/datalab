from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item


class Sample(Item):
    """A model for representing an experimental sample."""

    sample_id: str = Field(description="A machine-readable UUID for the sample.")

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemform: Optional[str] = Field(
        description="A string representation of the chemical formula associated with this sample."
    )
