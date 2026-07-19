from datetime import datetime, timezone
from enum import Enum

from pydantic import ConfigDict, Field

from pydatalab.models.utils import BaseModel, PyObjectId


class ExportStatus(str, Enum):
    """Status of an export task."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ExportTask(BaseModel):
    """Model for an export task."""

    task_id: str
    """Unique identifier for the export task"""

    collection_id: str | None = None
    """ID of the collection being exported"""

    item_id: str | None = None
    """ID of the item being exported"""

    export_type: str = "collection"
    """Type of export: 'collection' or 'item' or 'graph'"""

    status: ExportStatus = ExportStatus.PENDING
    """Current status of the task"""

    creator_id: PyObjectId
    """ID of the user who created the export"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    """When the task was created"""

    completed_at: datetime | None = None
    """When the task was completed"""

    file_path: str | None = None
    """Path to the generated .eln file"""

    error_message: str | None = None
    """Error message if status is ERROR"""

    model_config = ConfigDict(use_enum_values=True)
