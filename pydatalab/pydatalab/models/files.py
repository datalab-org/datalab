import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from pydatalab.models.entries import Entry


class File(Entry):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    type: str = Field("files", const="files", pattern="^files$")

    size: Optional[int] = Field(description="The size of the file on disk in bytes.")

    last_modified_remote: Optional[datetime.datetime] = Field(
        description="The last date/time at which the remote file was modified."
    )

    item_ids: List[str] = Field(description="A list of item IDs associated with this file.")

    blocks: List[str] = Field(description="A list of block IDs associated with this file.")

    name: str = Field(description="The filename on disk.")

    extension: str = Field(description="The file extension that the file was uploaded with.")

    original_name: Optional[str] = Field(description="The raw filename as uploaded.")

    location: Optional[str] = Field(description="The location of the file on disk.")

    url_path: Optional[str] = Field(description="The path to a remote file.")

    source: Optional[str] = Field(
        description="The source of the file, e.g. 'remote' or 'uploaded'."
    )

    time_added: datetime.datetime = Field(description="The timestamp for the original file upload.")

    metadata: Optional[Dict[Any, Any]] = Field(description="Any additional metadata.")

    representation: Optional[Any] = Field()

    source_server_name: Optional[str] = Field(
        description="The server name at which the file is stored."
    )

    source_path: Optional[str] = Field(description="The path to the file on the remote resource.")

    is_live: bool = Field(
        description="Whether or not the file should be watched for future updates."
    )

    class Config:
        extra = "allow"
