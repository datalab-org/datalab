from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class TaskType(str, Enum):
    EXPORT = "export"
    BLOCK_PROCESSING = "block_processing"


class TaskStage(BaseModel):
    timestamp: datetime = Field(..., description="When this stage occurred")
    message: str = Field(..., description="Description of this processing stage")
    level: Literal["info", "warning", "error"] = Field(
        default="info", description="Severity level of this stage"
    )


class Task(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    type: TaskType = Field(..., description="Type of task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    creator_id: str = Field(..., description="ID of the user who created the task")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When the task was created",
    )
    completed_at: datetime | None = Field(None, description="When completed")
    error_message: str | None = Field(None, description="Error message if status is ERROR")

    collection_id: str | None = Field(None, description="For export tasks: collection ID")
    item_id: str | None = Field(None, description="For export/block tasks: item ID")
    block_id: str | None = Field(None, description="For block tasks: block ID")
    export_type: str | None = Field(None, description="For export tasks: collection/sample/graph")
    file_path: str | None = Field(None, description="For export tasks: path to generated file")
    stages: list[TaskStage] = Field(
        default_factory=list,
        description="For block tasks: timestamped processing stages",
    )

    class Config:
        use_enum_values = True
