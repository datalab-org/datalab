"""Pydantic models for version control system."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator

from pydatalab.models.utils import PyObjectId, Refcode


class VersionAction(str, Enum):
    """Valid actions that can create a version snapshot."""

    CREATED = "created"
    MANUAL_SAVE = "manual_save"
    AUTO_SAVE = "auto_save"
    RESTORED = "restored"


class ItemVersion(BaseModel):
    """A complete snapshot of an item at a specific point in time.

    This model represents a version entry in the `item_versions` collection.
    Each version captures the complete state of an item, allowing users to
    view history and restore previous states.
    """

    refcode: Refcode = Field(..., description="The refcode of the item this version belongs to")
    version: int = Field(..., ge=1, description="Sequential version number (1-indexed)")
    timestamp: datetime = Field(
        ..., description="When this version was created (ISO format with timezone)"
    )
    action: VersionAction = Field(
        ...,
        description="The action that triggered this version: 'created' (item creation), "
        "'manual_save' (user save), 'auto_save' (system save), or 'restored' (version restore)",
    )
    user_id: PyObjectId | None = Field(
        None, description="User's ObjectId for efficient querying and indexing"
    )
    datalab_version: str = Field(
        ..., description="Version of datalab-server that created this snapshot"
    )
    data: dict = Field(..., description="Complete snapshot of the item data at this version")
    restored_from_version: PyObjectId | None = Field(
        None,
        description="ObjectId of the version that was restored from (only present if action='restored')",
    )

    @validator("restored_from_version")
    def validate_restored_from_version(cls, v, values):
        """Ensure restored_from_version is only present when action='restored'."""
        action = values.get("action")
        if action == VersionAction.RESTORED and v is None:
            raise ValueError("restored_from_version must be provided when action='restored'")
        if action != VersionAction.RESTORED and v is not None:
            raise ValueError(
                f"restored_from_version should only be present when action='restored', got action='{action}'"
            )
        return v


class VersionCounter(BaseModel):
    """Atomic counter for tracking version numbers per item.

    This model represents a document in the `version_counters` collection.
    It ensures atomic increment of version numbers to prevent race conditions.
    """

    refcode: Refcode = Field(..., description="The refcode this counter belongs to")
    counter: int = Field(
        1, ge=1, description="Current version counter value (1-indexed, matches version numbers)"
    )

    class Config:
        extra = "ignore"  # Allow MongoDB's _id field and other internal fields


class RestoreVersionRequest(BaseModel):
    """Request body for restoring a version."""

    version_id: str = Field(..., description="ObjectId string of the version to restore to")

    @validator("version_id")
    def validate_version_id_format(cls, v):
        """Validate that version_id is a valid ObjectId string."""
        try:
            from bson import ObjectId

            ObjectId(v)
        except Exception as e:
            raise ValueError(f"version_id must be a valid ObjectId string: {e}")
        return v

    class Config:
        extra = "forbid"


class CompareVersionsQuery(BaseModel):
    """Query parameters for comparing two versions."""

    v1: str = Field(..., description="ObjectId string of the first version")
    v2: str = Field(..., description="ObjectId string of the second version")

    @validator("v1", "v2")
    def validate_version_ids(cls, v):
        """Validate that version IDs are valid ObjectId strings."""
        try:
            from bson import ObjectId

            ObjectId(v)
        except Exception as e:
            raise ValueError(f"Version ID must be a valid ObjectId string: {e}")
        return v

    class Config:
        extra = "forbid"
