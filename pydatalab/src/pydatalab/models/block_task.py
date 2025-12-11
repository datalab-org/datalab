from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class BlockProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class BlockTask(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the block processing task")
    item_id: str = Field(..., description="ID of the item containing the block")
    block_id: str = Field(..., description="ID of the block being processed")
    status: BlockProcessingStatus = Field(
        default=BlockProcessingStatus.PENDING, description="Current status of the task"
    )
    creator_id: str = Field(..., description="ID of the user who created the task")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When the task was created",
    )
    completed_at: datetime | None = Field(None, description="When the task was completed")
    error_message: str | None = Field(None, description="Error message if status is ERROR")

    class Config:
        use_enum_values = True
