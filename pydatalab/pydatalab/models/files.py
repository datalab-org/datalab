import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator


class File(BaseModel):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    size: Optional[int] = Field(description="The size of the file on disk in bytes.")

    last_modified: Optional[Union[datetime.datetime, str]] = Field(
        description="The last date/time at which the stored file was modified."
    )

    last_modified_remote: Optional[Union[datetime.datetime, str]] = Field(
        description="The last date/time at which the remote file was modified."
    )

    version: int = Field(1, description="The version/revision number of the file.")

    item_ids: List[str] = Field(description="A list of item IDs associated with this file.")

    blocks: List[str] = Field(description="A list of block IDs associated with this file.")

    name: str = Field(description="The filename on disk.")

    extension: str = Field(description="The file extension that the file was uploaded with.")

    original_name: Optional[str] = Field(description="The raw filename as uploaded.")

    location: Optional[str] = Field(description="The location of the file on disk.")

    url_path: Optional[str] = Field(description="The path to a remote file.")

    type: Optional[str] = Field("files", const="files", pattern="^files$")

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

    @root_validator(pre=True)
    def pop_mongo_objectid(cls, values):
        if "_id" in values:
            values.pop("_id")

        return values

    class Config:
        extra = "forbid"
