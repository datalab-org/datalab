from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSubstanceInfo, HasSynthesisInfo
from pydatalab.models.utils import SampleStatus


class Sample(Item, HasSynthesisInfo, HasSubstanceInfo):
    """A model for representing an experimental sample."""

    type: Literal["samples"] = "samples"

    status: SampleStatus = Field(default=SampleStatus.ACTIVE)
    """The status of the sample, indicating its current state."""
