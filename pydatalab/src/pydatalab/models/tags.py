from typing import Literal

from pydatalab.models.entries import Entry


class Tag(Entry):
    """A tag that can be associated to other Entry entities.

    Tags are global: they are created and managed by administrators and can be
    used by every user. (Ownership/scope may be reintroduced later, e.g. via
    `HasOwner`.)
    """

    type: Literal["tags"] = "tags"

    name: str
    """A short, human-readable label for the tag."""

    description: str | None = None
    """An optional description of the tag, either in plain-text or a markup language."""

    color: str | None = None
    """An optional display color for the tag (e.g. a CSS hex string like `#f1c40f`)."""
