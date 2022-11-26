import datetime
from typing import List, Optional

from pydantic import Field, validator

from pydatalab.models.items import Item


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    date: datetime.datetime = Field(description="The creation timestamp of the item.")

    sample_id: Optional[str] = Field(description="a sample id provided by the user")

    chemform: Optional[str] = Field(
        description="A string representation of the chemical formula associated with this sample."
    )

    synthesis_constituents: List[dict] = Field(
        [], description="Dictionary giving amount and details of consituent items"
    )
    synthesis_description: Optional[str] = Field(description="Details of the sample synthesis")

    @validator("date", pre=True)
    def cast_to_datetime(cls, v):
        if isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)

        return v

    class Config:
        extra = "forbid"
