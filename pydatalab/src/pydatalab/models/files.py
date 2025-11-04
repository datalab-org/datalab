from typing import Any

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasOwner, HasRevisionControl
from pydatalab.models.utils import IsoformatDateTime


class File(Entry, HasOwner, HasRevisionControl):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    type: str = Field("files", const="files", pattern="^files$")

    size: int | None
    """The size of the file on disk in bytes."""

    last_modified_remote: IsoformatDateTime | None
    """The last date/time at which the remote file was modified."""

    item_ids: list[str]
    """A list of item IDs associated with this file."""

    blocks: list[str]
    """A list of block IDs associated with this file."""

    name: str
    """The filename on disk."""

    extension: str
    """The file extension that the file was uploaded with."""

    original_name: str | None
    """The raw filename as uploaded."""

    location: str | None
    """The location of the file on disk."""

    url_path: str | None
    """The path to a remote file."""

    source: str | None
    """The source of the file, e.g. 'remote' or 'uploaded'."""

    time_added: IsoformatDateTime
    """The timestamp for the original file upload."""

    metadata: dict[Any, Any] | None
    """Any additional metadata."""

    representation: Any | None

    source_server_name: str | None
    """The server name at which the file is stored."""

    source_path: str | None
    """The path to the file on the remote resource."""

    is_live: bool
    """Whether or not the file should be watched for future updates."""
