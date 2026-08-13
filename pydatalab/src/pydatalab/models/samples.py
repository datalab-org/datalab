from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSubstanceInfo, HasSynthesisInfo
from pydatalab.models.utils import SampleStatus


class Sample(Item, HasSynthesisInfo, HasSubstanceInfo):
    """A model for representing an experimental sample.

    A physical thing in the lab that can be created, characterised
    and connected to other items.
    """

    type: str = Field("samples", const="samples", pattern="^samples$")

    status: SampleStatus = Field(default=SampleStatus.ACTIVE)
    """The status of the sample, indicating its current state."""
