import datetime
from typing import Any

from pydantic import Field

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasOwner, HasRevisionControl
from pydatalab.models.utils import IsoformatDateTime


class File(Entry, HasOwner, HasRevisionControl):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    type: str = Field("files", const="files", pattern="^files$")

    size: int | None = Field(description="The size of the file on disk in bytes.")

    last_modified_remote: IsoformatDateTime | None = Field(
        description="The last date/time at which the remote file was modified."
    )

    item_ids: list[str] = Field(description="A list of item IDs associated with this file.")

    blocks: list[str] = Field(description="A list of block IDs associated with this file.")

    name: str = Field(description="The filename on disk.")

    extension: str = Field(description="The file extension that the file was uploaded with.")

    original_name: str | None = Field(description="The raw filename as uploaded.")

    location: str | None = Field(description="The location of the file on disk.")

    url_path: str | None = Field(description="The path to a remote file.")

    source: str | None = Field(description="The source of the file, e.g. 'remote' or 'uploaded'.")

    time_added: datetime.datetime = Field(description="The timestamp for the original file upload.")

    metadata: dict[Any, Any] | None = Field(description="Any additional metadata.")

    representation: Any | None = Field()

    source_server_name: str | None = Field(
        description="The server name at which the file is stored."
    )

    source_path: str | None = Field(description="The path to the file on the remote resource.")

    is_live: bool = Field(
        description="Whether or not the file should be watched for future updates."
    )
