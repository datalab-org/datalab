# This file was edited with the assistance of an AI model and requires human review from the contributor.
from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSubstanceInfo, HasSynthesisInfo
from pydatalab.models.utils import SampleStatus


class Sample(Item, HasSynthesisInfo, HasSubstanceInfo):
    """A model for representing an experimental sample.

    A physical thing in the lab that can be created, characterised
    and connected to other items.
    """

    type: Literal["samples"] = "samples"

    status: SampleStatus = Field(
        default=SampleStatus.ACTIVE,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """The status of the sample, indicating its current state."""
