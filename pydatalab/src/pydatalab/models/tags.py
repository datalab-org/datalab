from typing import Literal

from pydantic import model_validator

from pydatalab.models.entries import Entry
from pydatalab.models.utils import AccessScope, PyObjectId


class Tag(Entry):
    """A tag that can be associated to other Entry entities.

    Tags have a `scope` that controls who can list, use and manage them:

    - `AccessScope.GLOBAL`: available to (and usable by) everyone; created and
      managed by administrators only. Global tags have no `owner`.
    - `AccessScope.USER`: a user-defined tag owned by exactly one user; only that
      user can list, use, edit and delete it.

    Names are only required to be unique within a scope.
    """

    type: Literal["tags"] = "tags"

    name: str
    """A short, human-readable label for the tag."""

    description: str | None = None
    """An optional description of the tag, either in plain-text or a markup language."""

    color: str | None = None
    """An optional display color for the tag (e.g. a CSS hex string like `#f1c40f`)."""

    scope: AccessScope
    """The scope controlling who can list, use and manage this tag (required)."""

    owner: PyObjectId | None = None
    """The database ID of the user that owns this tag."""

    @model_validator(mode="after")
    def _check_scope_owner_consistency(self):
        """Ensure `scope` and `owner` are mutually consistent."""
        if self.scope == AccessScope.USER and self.owner is None:
            raise ValueError("A user-scoped tag must have an owner.")
        if self.scope == AccessScope.GLOBAL and self.owner is not None:
            raise ValueError("A global tag cannot have an owner.")
        return self
