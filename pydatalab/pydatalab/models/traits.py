from typing import List, Optional

from pydantic import BaseModel, Field

from pydatalab.models.people import Person
from pydatalab.models.utils import PyObjectId


class HasOwner(BaseModel):

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""
