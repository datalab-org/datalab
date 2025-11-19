from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo


class Sample(Item, HasSynthesisInfo):
    """A model for representing an experimental sample."""

    type: Literal["samples"] = "samples"

    chemform: str | None = Field(
        None,
        examples=["Na3P", "LiNiO2@C"],
        description="A string representation of the chemical formula or composition associated with this sample.",
    )
