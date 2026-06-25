"""Pydantic models for version control system."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from pydatalab.models.utils import BaseModel, PyObjectId, Refcode


class VersionAction(str, Enum):
    """Valid actions that can create a version snapshot."""

    CREATED = "created"
    MANUAL_SAVE = "manual_save"
    AUTO_SAVE = "auto_save"
    RESTORED = "restored"
    AGENT_SAVE = "agent_save"


class ItemVersion(BaseModel):
    """A complete snapshot of an item at a specific point in time.

    This model represents a version entry in the `item_versions` collection.
    Each version captures the complete state of an item, allowing users to
    view history and restore previous states.
    """

    refcode: Refcode
    """The refcode of the item this version belongs to"""

    version: int = Field(ge=1)
    """Sequential version number (1-indexed)"""

    timestamp: datetime
    """When this version was created (ISO format with timezone)"""

    action: VersionAction
    """The action that triggered this version: 'created' (item creation), 'manual_save' (user save), 'auto_save' (system save), or 'restored' (version restore)"""

    user_id: PyObjectId | None = None
    """User's ObjectId for efficient querying and indexing"""

    creator: dict | None = None
    """Inlined information about the user who created this version (e.g., name)"""

    datalab_version: str
    """Version of datalab-server that created this snapshot"""

    data: dict
    """Complete snapshot of the item data at this version"""

    restored_from_version: PyObjectId | None = None
    """ObjectId of the version that was restored from (only present if action='restored')"""

    user_agent: str | None = None
    """User agent string of the client that triggered this version. Will only be stored if it matches a known value from the datalab ecosystem."""

    def to_mongo_doc(self) -> dict[str, Any]:
        """Serialise for insertion into MongoDB, preserving None values in `data`.

        Pydantic v2 model_dump(exclude_none=True) recurses into nested dicts and
        would strip None-valued fields from the item snapshot in `data`. Those keys
        must be present so that a $set restore can explicitly clear fields that were
        None in the snapshot. All other top-level None fields (user_id, creator, etc.)
        are still excluded since they are optional metadata.
        """
        d = self.model_dump(exclude_none=True)
        d["data"] = self.data
        return d

    @model_validator(mode="after")
    def validate_restored_from_version(self):
        """Ensure restored_from_version is only present when action='restored'."""
        if self.action == VersionAction.RESTORED and self.restored_from_version is None:
            raise ValueError("restored_from_version must be provided when action='restored'")
        if self.action != VersionAction.RESTORED and self.restored_from_version is not None:
            raise ValueError(
                f"restored_from_version should only be present when action='restored', got action='{self.action}'"
            )
        return self


class VersionCounter(BaseModel):
    """Atomic counter for tracking version numbers per item.

    This model represents a document in the `version_counters` collection.
    It ensures atomic increment of version numbers to prevent race conditions.
    """

    refcode: Refcode
    """The refcode this counter belongs to"""

    counter: int = Field(1, ge=1)
    """Current version counter value (1-indexed, matches version numbers)"""

    model_config = ConfigDict(extra="ignore")


class RestoreVersionRequest(BaseModel):
    """Request body for restoring a version."""

    version_id: PyObjectId
    """ObjectId string of the version to restore to"""

    model_config = ConfigDict(extra="forbid")


class CompareVersionsQuery(BaseModel):
    """Query parameters for comparing two versions."""

    v1: PyObjectId
    """ObjectId string of the first version"""

    v2: PyObjectId
    """ObjectId string of the second version"""

    model_config = ConfigDict(extra="forbid")
