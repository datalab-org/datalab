from typing import Any, Dict, List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasOwner, HasRevisionControl
from pydatalab.models.utils import IsoformatDateTime


class File(Entry, HasOwner, HasRevisionControl):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    type: str = Field("files", const="files", pattern="^files$")

    size: Optional[int]
    """The size of the file on disk in bytes."""

    last_modified_remote: Optional[IsoformatDateTime]
    """The last date/time at which the remote file was modified."""

    item_ids: List[str]
    """A list of item IDs associated with this file."""

    blocks: List[str]
    """A list of block IDs associated with this file."""

    name: str
    """The filename on disk."""

    extension: str
    """The file extension that the file was uploaded with."""

    original_name: Optional[str]
    """The raw filename as uploaded."""

    location: Optional[str]
    """The location of the file on disk."""

    url_path: Optional[str]
    """The path to a remote file."""

    source: Optional[str]
    """The source of the file, e.g. 'remote' or 'uploaded'."""

    time_added: IsoformatDateTime
    """The timestamp for the original file upload."""

    metadata: Optional[Dict[Any, Any]]
    """Any additional metadata."""

    representation: Optional[Any]

    source_server_name: Optional[str]
    """The server name at which the file is stored."""

    source_path: Optional[str]
    """The path to the file on the remote resource."""

    is_live: bool
    """Whether or not the file should be watched for future updates."""
