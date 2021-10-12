import datetime
from typing import Optional

from pydantic import Field

from pydatalab.models.items import Item, validator


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    date: datetime.datetime = Field(description="The creation timestamp of the item.")

    sample_id: Optional[str] = Field(description="a sample id provided by the user")

    chemform: Optional[str] = Field(
        description="A string representation of the chemical formula associated with this sample."
    )

    @validator("date", pre=True)
    def cast_to_datetime(cls, v):
        if isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)

        return v
