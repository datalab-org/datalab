import abc

from pydantic import field_validator

from pydatalab.models.entries import Entry

# Importing `files` here resolves the deferred `File` annotation on `HasFiles`
# before any `Item` subclass is built.
from pydatalab.models.files import File  # noqa: F401
from pydatalab.models.traits import (
    HasBlocks,
    HasFiles,
    HasOwner,
    HasRevisionControl,
    IsCollectable,
)
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    Refcode,
)


class Item(Entry, HasOwner, HasRevisionControl, IsCollectable, HasBlocks, HasFiles, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints.

    `Item` is the abstract base shared by every physical item type: samples, cells,
    starting materials and equipment. `item_id` is normally the only required field;
    the remaining fields are either optional metadata or bookkeeping that the server
    populates itself.
    """

    refcode: Refcode | None = None
    """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`) and a locally unique string, ideally created with some consistent scheme."""

    item_id: HumanReadableIdentifier
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

    description: str | None = None
    """A description of the item, either in plain-text or a markup language."""

    date: IsoformatDateTime | None = None
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: str | None = None
    """An optional human-readable/usable name for the entry."""

    status: str | None = None
    """The status of the item, with allowed values defined by the specific item class."""

    @field_validator("refcode", mode="before")
    @classmethod
    def refcode_validator(cls, v):
        """Generate a refcode if not provided."""

        if v:
            prefix = None
            id = None
            prefix, id = v.split(":")
            if prefix is None or id is None:
                raise ValueError(f"refcode missing prefix or ID {id=}, {prefix=} from {v=}")

        return v
