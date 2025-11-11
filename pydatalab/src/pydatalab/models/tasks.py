from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import Field, validator

from pydatalab.models.utils import BaseModel, PyObjectId


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class TaskType(str, Enum):
    EXPORT = "export"
    BLOCK_PROCESSING = "block_processing"


class TaskStage(BaseModel):
    timestamp: datetime
    """When this stage occurred"""

    message: str
    """Description of this processing stage"""

    level: Literal["info", "warning", "error"] = "info"
    """Severity level of this stage"""

    detail: str | None = None
    """Optional detailed information about this stage"""


class TaskSpec(BaseModel):
    pass


class ExportTaskSpec(TaskSpec):
    collection_id: str | None = None
    """Collection ID being exported"""

    item_id: str | None = None
    """Item ID being exported"""

    export_type: str
    """Type of export: collection/item/graph"""

    file_path: str | None = None
    """Path to generated .eln file"""

    stages: list[TaskStage] = Field(default_factory=list)
    """Timestamped processing stages"""


class BlockProcessingTaskSpec(TaskSpec):
    item_id: str
    """Item ID containing the block"""

    block_id: str
    """Block ID being processed"""

    stages: list[TaskStage] = Field(default_factory=list)
    """Timestamped processing stages"""


class Task(BaseModel):
    task_id: str
    """Unique identifier for the task"""

    type: TaskType
    """Type of task"""

    status: TaskStatus = TaskStatus.PENDING
    """Current status"""

    creator_id: PyObjectId
    """ID of the user who created the task"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    """When the task was created"""

    completed_at: datetime | None = None
    """When completed"""

    error_message: str | None = None
    """Error message if status is ERROR"""

    spec: ExportTaskSpec | BlockProcessingTaskSpec
    """Task-specific data"""

    @validator("spec", pre=True, always=True)
    def validate_spec_type(cls, v, values):
        task_type = values.get("type")

        if task_type == TaskType.EXPORT:
            if not isinstance(v, ExportTaskSpec):
                return ExportTaskSpec(**v) if isinstance(v, dict) else v
        elif task_type == TaskType.BLOCK_PROCESSING:
            if not isinstance(v, BlockProcessingTaskSpec):
                return BlockProcessingTaskSpec(**v) if isinstance(v, dict) else v

        return v

    class Config:
        use_enum_values = True
