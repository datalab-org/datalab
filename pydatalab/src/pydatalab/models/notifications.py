from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, root_validator

from pydatalab.models.entries import Entry
from pydatalab.models.utils import JSON_ENCODERS, PyObjectId


class NotificationLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"
    CRITICAL = "critical"

    @property
    def priority(self) -> int:
        return {
            NotificationLevel.LOW: 10,
            NotificationLevel.NORMAL: 20,
            NotificationLevel.IMPORTANT: 30,
            NotificationLevel.URGENT: 40,
            NotificationLevel.CRITICAL: 50,
        }[self]


class NotificationGroupPolicy(str, Enum):
    ONCE = "once"
    WINDOW = "window"


class NotificationGrouping(BaseModel):
    """Rules for grouping repeated notification occurrences."""

    key: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Stable key used to group repeated notifications from the same thing.",
    )
    policy: NotificationGroupPolicy = Field(
        NotificationGroupPolicy.WINDOW,
        description="How repeated notification occurrences should be grouped.",
    )
    window_seconds: int | None = Field(
        86400,
        ge=1,
        description=(
            "Minimum interval before a grouped notification can create a new notification document."
        ),
    )
    max_occurrences: int = Field(
        100,
        ge=1,
        description="Maximum number of occurrences before a new notification document is created.",
    )

    @root_validator
    def validate_grouping_policy(cls, values):
        policy = NotificationGroupPolicy(values.get("policy"))
        if policy == NotificationGroupPolicy.WINDOW and values.get("window_seconds") is None:
            raise ValueError("window_seconds must be provided for window grouping.")
        if policy == NotificationGroupPolicy.ONCE:
            values["window_seconds"] = None
        return values

    class Config:
        json_encoders = JSON_ENCODERS
        use_enum_values = True


class NotificationOccurrence(BaseModel):
    """A single occurrence represented by a grouped notification."""

    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    summary: str | None = Field(None, max_length=1000)
    message: str | None = Field(None, max_length=5000)
    level: NotificationLevel = Field(NotificationLevel.NORMAL)
    is_new: bool = Field(
        False,
        description="Whether this occurrence arrived since the notification was last read.",
    )

    class Config:
        json_encoders = JSON_ENCODERS
        use_enum_values = True


class Notification(Entry):
    """A notification addressed to one user."""

    type: str = Field("notifications", const=True)
    recipient_id: PyObjectId = Field(..., description="ID of the user receiving the notification")
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = Field(
        None,
        max_length=1000,
        description="Short text shown in compact notification lists.",
    )
    message: str | None = Field(None, max_length=5000)
    level: NotificationLevel = Field(NotificationLevel.NORMAL)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    created_by: PyObjectId | None = Field(None, description="User ID that created the notification")
    read_at: datetime | None = None
    archived_at: datetime | None = None
    grouping: NotificationGrouping | None = None
    occurrence_count: int = Field(1, ge=1)
    last_occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    occurrences: list[NotificationOccurrence] | None = Field(
        None,
        description="Individual occurrence details for grouped notifications.",
    )

    class Config(Entry.Config):
        use_enum_values = True
