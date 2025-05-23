from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo
from pydatalab.models.utils import SampleStatus


class Sample(Item, HasSynthesisInfo):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemform: str | None = Field(example=["Na3P", "LiNiO2@C"])
    """A string representation of the chemical formula or composition associated with this sample."""

    status: SampleStatus = Field(default=SampleStatus.ACTIVE)
    """The status of the sample, indicating its current state."""
