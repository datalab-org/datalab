"""Application-scoped discovery and registration of tool providers."""

import re
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.login import is_browser_session_user
from pydatalab.models.people import AccountStatus

from .auth import request_origin_is_allowed
from .base import InAppToolUI, ToolContext, ToolMetadata, ToolProvider, ToolRouteAuth

if TYPE_CHECKING:
    from flask import Flask

TOOL_REGISTRY_EXTENSION = "pydatalab.tools"
TOOL_ENTRY_POINT_GROUP = "pydatalab.tools"
TOOL_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class ToolRegistry:
    """Registry of validated installed tool providers."""

    def __init__(self) -> None:
        self._providers: dict[str, ToolProvider] = {}
        self._failed_provider_ids: set[str] = set()

    def register(self, provider: ToolProvider, entry_point_name: str | None = None) -> None:
        """Validate and register ``provider``."""
        if not isinstance(provider, ToolProvider):
            raise TypeError("Tool plugins must be ToolProvider instances")
        if not isinstance(provider.metadata, ToolMetadata):
            raise TypeError("Tool provider metadata must be a ToolMetadata instance")
        if provider.blueprint is not None and not isinstance(provider.blueprint, Blueprint):
            raise TypeError("Tool provider blueprint must be a Flask Blueprint")
        if not isinstance(provider.route_auth, ToolRouteAuth):
            raise TypeError("Tool provider route_auth must be a ToolRouteAuth value")
        if (
            provider.blueprint is not None
            and provider.route_auth is ToolRouteAuth.SERVICE
            and type(provider).authenticate_service_request
            is ToolProvider.authenticate_service_request
        ):
            raise ValueError(
                "Service-authenticated tool providers must implement authenticate_service_request()"
            )
        if isinstance(provider.metadata.ui, InAppToolUI) and provider.blueprint is None:
            raise ValueError("In-app tools must serve their entrypoint from a plugin blueprint")
        if not TOOL_ID_PATTERN.fullmatch(provider.id):
            raise ValueError(
                f"Tool provider ID {provider.id!r} must be a lowercase hyphenated slug"
            )
        if entry_point_name is not None and entry_point_name != provider.id:
            raise ValueError(
                f"Tool entry point {entry_point_name!r} does not match provider ID {provider.id!r}"
            )
        if provider.id in self._providers:
            raise ValueError(f"Duplicate tool provider ID {provider.id!r}")

        self._providers[provider.id] = provider

    def get(self, tool_id: str) -> ToolProvider | None:
        """Return a registered provider by ID."""
        if tool_id in self._failed_provider_ids:
            return None
        return self._providers.get(tool_id)

    def mark_failed(self, tool_id: str) -> None:
        """Prevent a provider with failed application setup from being used."""
        self._failed_provider_ids.add(tool_id)

    def is_enabled(self, tool_id: str) -> bool:
        """Return whether an installed provider is globally usable."""
        if self.get(tool_id) is None:
            return False
        return tool_id not in CONFIG.TOOLS.DISABLED

    def _is_available(self, provider: ToolProvider, context: ToolContext) -> bool:
        if not self.is_enabled(provider.id):
            return False
        try:
            return provider.is_available(context)
        except Exception:
            LOGGER.exception(
                "Tool provider %r failed its current-user availability check",
                provider.id,
            )
            return False

    def available_for(self, context: ToolContext) -> list[ToolProvider]:
        """Return enabled providers whose availability check succeeds."""
        return [
            provider
            for provider in self._providers.values()
            if self._is_available(provider, context)
        ]

    def available_provider(
        self,
        tool_id: str,
        context: ToolContext,
    ) -> ToolProvider | None:
        """Return one provider only when enabled and available to ``context``."""
        provider = self.get(tool_id)
        if provider is None:
            return None
        return provider if self._is_available(provider, context) else None

    @property
    def providers(self) -> tuple[ToolProvider, ...]:
        """Return all registered providers in deterministic registration order."""
        return tuple(self._providers.values())


def create_tool_registry() -> ToolRegistry:
    """Create a fresh registry for one Flask application."""
    registry = ToolRegistry()
    configured_positions = {
        tool_id: position for position, tool_id in enumerate(CONFIG.TOOLS.ORDER)
    }
    for entry_point in sorted(
        entry_points(group=TOOL_ENTRY_POINT_GROUP),
        key=lambda candidate: (
            configured_positions.get(candidate.name, len(configured_positions)),
            candidate.name,
        ),
    ):
        try:
            registry.register(entry_point.load()(), entry_point_name=entry_point.name)
        except Exception:
            LOGGER.exception("Unable to load tool plugin entry point %r", entry_point.name)

    return registry


def register_tool_blueprints(app: "Flask", registry: ToolRegistry) -> None:
    """Register optional provider-owned routes under the tool plugin namespace."""
    from pydatalab.routes import __api_version__

    major, minor, patch = __api_version__.split(".")
    versions = ("", f"v{major}", f"v{major}.{minor}", f"v{major}.{minor}.{patch}")
    route_providers: dict[str, ToolProvider] = {}

    @app.before_request
    def authenticate_tool_blueprint_request():
        """Apply the provider's route policy before dispatching its blueprint."""
        provider = route_providers.get(request.blueprint or "")
        if provider is None:
            return None
        if not registry.is_enabled(provider.id):
            return jsonify({"status": "error", "message": "Tool not available"}), 404

        if provider.route_auth is ToolRouteAuth.BROWSER:
            if request.method == "OPTIONS":
                return None
            if not current_user.is_authenticated:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            if current_user.account_status != AccountStatus.ACTIVE or not is_browser_session_user(
                current_user
            ):
                return (
                    jsonify({"status": "error", "message": "A browser session is required"}),
                    403,
                )
            if request.method not in {"GET", "HEAD"} and not request_origin_is_allowed():
                return jsonify({"status": "error", "message": "Untrusted request origin"}), 403
            return None

        try:
            authenticated = provider.authenticate_service_request() is True
        except Exception:
            LOGGER.exception(
                "Tool provider %r failed to authenticate a service request", provider.id
            )
            authenticated = False
        if not authenticated:
            return jsonify({"status": "error", "message": "Invalid service credentials"}), 401
        return None

    for provider in registry.providers:
        if provider.blueprint is None:
            continue
        if not registry.is_enabled(provider.id):
            continue
        try:
            for version in versions:
                api_prefix = f"{CONFIG.ROOT_PATH}{version}".rstrip("/")
                prefix = f"{api_prefix}/tools/plugins/{provider.id}"
                registration_name = f"{version}/tool-plugin-{provider.id}"
                app.register_blueprint(
                    provider.blueprint,
                    url_prefix=prefix,
                    name=registration_name,
                )
                route_providers[registration_name] = provider
        except Exception:
            LOGGER.exception("Unable to register routes for tool provider %r", provider.id)
            registry.mark_failed(provider.id)
