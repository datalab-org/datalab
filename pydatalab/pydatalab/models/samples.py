import datetime
from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item, validator


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    sample_id: str = Field(description="A machine-readable UUID for the sample.")

    date: datetime.datetime = Field(description="The creation timestamp of the item.")

    chemform: Optional[str] = Field(
        description="A string representation of the chemical formula associated with this sample."
    )

    @validator("date", pre=True)
    def cast_to_datetime(cls, v):
        if isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)

        return v
