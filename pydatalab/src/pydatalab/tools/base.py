"""Stable public interfaces for datalab tool providers."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Literal, Protocol, Self
from urllib.parse import urlsplit

from flask import Blueprint
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

TOOL_ENTRYPOINT_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TOOL_ACTION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ToolOpenMode = Literal["same_tab", "new_tab"]


class _ImmutableToolModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ItemTableSelectionAction(_ImmutableToolModel):
    """A tool action offered for selected rows in configured item tables."""

    kind: Literal["item-table-selection"] = "item-table-selection"
    id: str
    label: str
    tables: tuple[Literal["samples", "inventory", "equipment", "collection-items"], ...]
    min_items: StrictInt = 1
    max_items: StrictInt = 100

    @field_validator("id")
    @classmethod
    def id_is_lowercase_slug(cls, value):
        if not TOOL_ACTION_ID_PATTERN.fullmatch(value):
            raise ValueError("Tool action IDs must be lowercase hyphenated slugs")
        return value

    @field_validator("label")
    @classmethod
    def label_is_non_empty(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Tool action labels must not be empty")
        return value

    @field_validator("tables")
    @classmethod
    def tables_are_non_empty_and_unique(cls, value):
        if not value:
            raise ValueError("Tool actions must declare at least one table")
        if len(value) != len(set(value)):
            raise ValueError("Tool action tables must not contain duplicates")
        return value

    @model_validator(mode="after")
    def selection_limits_are_valid(self) -> Self:
        if self.min_items < 1 or self.max_items > 100 or self.min_items > self.max_items:
            raise ValueError("Tool action limits must satisfy 1 <= min_items <= max_items <= 100")
        return self


class ItemSelection(_ImmutableToolModel):
    """One validated table-selection action and its ordered item refcodes."""

    action_id: str
    item_refcodes: tuple[StrictStr, ...]

    @field_validator("action_id")
    @classmethod
    def action_id_is_lowercase_slug(cls, value):
        if not TOOL_ACTION_ID_PATTERN.fullmatch(value):
            raise ValueError("Tool action IDs must be lowercase hyphenated slugs")
        return value

    @field_validator("item_refcodes")
    @classmethod
    def item_refcodes_are_non_empty_and_unique(cls, value):
        if not value:
            raise ValueError("An item selection must contain at least one refcode")
        if len(value) > 100:
            raise ValueError("An item selection cannot contain more than 100 refcodes")
        if any(not refcode or refcode != refcode.strip() for refcode in value):
            raise ValueError("Selected item refcodes must be non-empty canonical strings")
        if len(value) != len(set(value)):
            raise ValueError("Selected item refcodes must not contain duplicates")
        return value


class ToolRouteAuth(str, Enum):
    """Authentication policy applied to every route in a provider blueprint."""

    BROWSER = "browser"
    SERVICE = "service"


class BaseToolUI(_ImmutableToolModel):
    """Shared configuration for a tool's user interface."""

    open_mode: _ToolOpenMode


class StandaloneToolUI(BaseToolUI):
    """A tool UI that runs outside the datalab web application."""

    kind: Literal["standalone"] = "standalone"
    open_mode: _ToolOpenMode = "new_tab"


class InAppToolUI(BaseToolUI):
    """A trusted frontend bundle mounted inside the datalab web application."""

    kind: Literal["in_app"] = "in_app"
    open_mode: _ToolOpenMode = "same_tab"
    entrypoint: str = "frontend/tool.js"
    sdk_version: Literal[1] = 1

    @field_validator("entrypoint")
    @classmethod
    def entrypoint_is_namespaced_relative_path(cls, value):
        parsed = urlsplit(value)
        segments = value.split("/")
        if (
            value != value.strip()
            or value.startswith("/")
            or "\\" in value
            or "%" in value
            or parsed.scheme
            or parsed.netloc
            or parsed.query
            or parsed.fragment
            or any(not TOOL_ENTRYPOINT_SEGMENT_PATTERN.fullmatch(segment) for segment in segments)
            or not segments[-1].endswith(".js")
        ):
            raise ValueError(
                "In-app tool entrypoints must be canonical relative JavaScript paths below the "
                "provider namespace"
            )
        return value


class ToolMetadata(_ImmutableToolModel):
    """User-facing metadata returned by the tool catalog."""

    name: str
    description: str
    version: str | None = None
    icon: str = "laptop-code"
    ui: StandaloneToolUI | InAppToolUI = Field(
        default_factory=StandaloneToolUI,
        discriminator="kind",
    )
    launch_actions: tuple[ItemTableSelectionAction, ...] = ()

    @field_validator("launch_actions")
    @classmethod
    def launch_action_ids_are_unique(cls, value):
        action_ids = [action.id for action in value]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("Tool action IDs must be unique within a provider")
        return value


@dataclass(frozen=True)
class ToolContext:
    """Restricted, immutable current-user data passed to trusted providers."""

    user_id: str
    display_name: str | None
    role: str
    group_ids: tuple[str, ...]


class ToolLaunchGrantIssuer(Protocol):
    """Capability offered to a provider for issuing current-user tool launch grants."""

    def issue(self, client_id: str, lifetime_seconds: int = 60) -> str:
        """Create and return a raw, single-use launch code."""


class ToolProvider:
    """Base class implemented by installed tool providers."""

    id: ClassVar[str]
    metadata: ClassVar[ToolMetadata]
    blueprint: ClassVar[Blueprint | None] = None
    route_auth: ClassVar[ToolRouteAuth] = ToolRouteAuth.BROWSER

    def is_available(self, context: ToolContext) -> bool:
        """Return whether this provider is catalogued and launchable for ``context``."""
        return True

    def authenticate_service_request(self) -> bool:
        """Authenticate one request when ``route_auth`` is ``SERVICE``.

        Service-authenticated providers must override this method. Browser
        authentication is supplied by the tool framework.
        """
        return False

    def launch(
        self,
        context: ToolContext,
        grants: ToolLaunchGrantIssuer,
    ) -> str | None:
        """Prepare and return a launch for ``context``."""
        return None
