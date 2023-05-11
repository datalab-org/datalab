from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pydatalab.models.people import Person
from pydatalab.models.utils import PyObjectId


class HasOwner(BaseModel):

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""


class HasRevisionControl(BaseModel):

    revision: int = 1
    """The revision number of the entry."""

    revisions: Optional[Dict[int, Any]] = None
    """An optional mapping from old revision numbers to the model state at that revision."""
