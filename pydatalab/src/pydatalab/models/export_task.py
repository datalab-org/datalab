from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from pydatalab.models.utils import PyObjectId


class ExportStatus(str, Enum):
    """Status of an export task."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ExportTask(BaseModel):
    """Model for an export task."""

    task_id: str = Field(..., description="Unique identifier for the export task")
    collection_id: str | None = Field(None, description="ID of the collection being exported")
    item_id: str | None = Field(None, description="ID of the item being exported")
    export_type: str = Field(
        default="collection", description="Type of export: 'collection' or 'item' or 'graph'"
    )
    status: ExportStatus = Field(
        default=ExportStatus.PENDING, description="Current status of the task"
    )
    creator_id: PyObjectId = Field(..., description="ID of the user who created the export")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When the task was created",
    )
    completed_at: datetime | None = Field(None, description="When the task was completed")
    file_path: str | None = Field(None, description="Path to the generated .eln file")
    error_message: str | None = Field(None, description="Error message if status is ERROR")

    class Config:
        use_enum_values = True
