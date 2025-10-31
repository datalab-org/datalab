import abc

from pydantic import Field, validator

from pydatalab.models.entries import Entry
from pydatalab.models.files import File
from pydatalab.models.traits import (
    HasBlocks,
    HasOwner,
    HasRevisionControl,
    IsCollectable,
)
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    PyObjectId,
    Refcode,
)


class Item(Entry, HasOwner, HasRevisionControl, IsCollectable, HasBlocks, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    refcode: Refcode = None  # type: ignore
    """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`)
    and a locally unique string, ideally created with some consistent scheme.
    """

    item_id: HumanReadableIdentifier
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

    description: str | None
    """A description of the item, either in plain-text or a markup language."""

    date: IsoformatDateTime | None
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: str | None
    """An optional human-readable/usable name for the entry."""

    files: list[File] | None
    """Any files attached to this sample."""

    file_ObjectIds: list[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""

    status: str | None
    """The status of the item, with allowed values defined by the specific item class."""

    @validator("refcode", pre=True, always=True)
    def refcode_validator(cls, v):
        """Generate a refcode if not provided."""

        if v:
            prefix = None
            id = None
            prefix, id = v.split(":")
            if prefix is None or id is None:
                raise ValueError(f"refcode missing prefix or ID {id=}, {prefix=} from {v=}")

        return v
