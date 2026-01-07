from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, validator

from pydatalab.models.utils import PyObjectId


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


class TaskSpec(BaseModel):
    pass


class ExportTaskSpec(TaskSpec):
    collection_id: str | None = Field(None, description="Collection ID being exported")
    item_id: str | None = Field(None, description="Item ID being exported")
    export_type: str = Field(..., description="Type of export: collection/item/graph")
    file_path: str | None = Field(None, description="Path to generated .eln file")


class BlockProcessingTaskSpec(TaskSpec):
    item_id: str = Field(..., description="Item ID containing the block")
    block_id: str = Field(..., description="Block ID being processed")
    stages: list[TaskStage] = Field(
        default_factory=list, description="Timestamped processing stages"
    )


class Task(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    type: TaskType = Field(..., description="Type of task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    creator_id: PyObjectId = Field(..., description="ID of the user who created the task")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When the task was created",
    )
    completed_at: datetime | None = Field(None, description="When completed")
    error_message: str | None = Field(None, description="Error message if status is ERROR")
    spec: ExportTaskSpec | BlockProcessingTaskSpec = Field(..., description="Task-specific data")

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
