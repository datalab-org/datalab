from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.utils import Constituent, InlineSubstance, SampleStatus
from pydatalab.models.traits import HasSynthesisInfo


class Sample(Item, HasSynthesisInfo):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemform: Optional[str] = Field(example=["Na3P", "LiNiO2@C"])
    """A string representation of the chemical formula or composition associated with this sample."""

    status: SampleStatus = Field(default=SampleStatus.PLANNED)
    """The status of the sample, indicating its current state."""