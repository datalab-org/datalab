import abc
from typing import Any, Dict, List, Optional

from pydantic import Field, validator

from pydatalab.models.entries import Entry
from pydatalab.models.people import Person
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
    Refcode,
)


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    refcode: Refcode = None  # type: ignore
    """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`)
    and a locally unique string, ideally created with some consistent scheme.
    """

    item_id: HumanReadableIdentifier
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

    creator_ids: List[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""

    description: Optional[str]
    """A description of the item, either in plain-text or a markup language."""

    date: Optional[IsoformatDateTime]
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: Optional[str]
    """An optional human-readable/usable name for the entry."""

    blocks_obj: Dict[str, Any] = Field({})
    """A mapping from block ID to block data."""

    display_order: List[str] = Field([])
    """The order in which to display block data in the UI."""

    files: Optional[List[str]]
    """Any files attached to this sample."""

    file_ObjectIds: List[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""

    @validator("refcode", pre=True, always=True)
    def refcode_validator(cls, v):
        """Generate a refcode if not provided; check that the refcode has the correct prefix if provided."""

        from pydatalab.config import CONFIG

        if v and not v.startswith(f"{CONFIG.IDENTIFIER_PREFIX}:"):
            raise ValueError(f"refcode missing prefix {CONFIG.IDENTIFIER_PREFIX!r}")

        return v
