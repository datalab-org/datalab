"""Current-user catalog and launch routes for tools."""

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from pydatalab.logger import LOGGER
from pydatalab.login import is_browser_session_user, is_tool_access_token_user
from pydatalab.models.people import AccountStatus
from pydatalab.permissions import active_users_or_get_only
from pydatalab.tools.auth import request_origin_is_allowed
from pydatalab.tools.base import (
    ItemSelection,
    StandaloneToolUI,
    ToolContext,
    ToolProvider,
)
from pydatalab.tools.grants import (
    BoundToolLaunchGrantIssuer,
    consume_tool_selection_code,
)
from pydatalab.tools.registry import TOOL_REGISTRY_EXTENSION, ToolRegistry

from .info import Attributes, Data, JSONAPIResponse, Meta

TOOLS = Blueprint("tools", __name__)


def _active_tool_context() -> ToolContext | None:
    if not current_user.is_authenticated or current_user.account_status != AccountStatus.ACTIVE:
        return None

    groups = current_user.groups or []
    return ToolContext(
        user_id=str(current_user.person.immutable_id),
        display_name=current_user.display_name,
        role=current_user.role.value,
        group_ids=tuple(str(group.immutable_id) for group in groups),
    )


def _registry() -> ToolRegistry:
    return current_app.extensions[TOOL_REGISTRY_EXTENSION]


def _launch_selection(provider: ToolProvider) -> ItemSelection | None:
    payload = request.get_json(silent=True)
    if payload is None:
        if request.get_data(cache=True):
            raise ValueError("The launch request must contain a JSON object")
        return None
    if not isinstance(payload, dict) or set(payload) - {"action", "items"}:
        raise ValueError("The launch request contains unsupported fields")

    action_id = payload.get("action")
    item_refcodes = payload.get("items")
    if action_id is None and item_refcodes is None:
        return None
    if not isinstance(action_id, str) or not isinstance(item_refcodes, list):
        raise ValueError("A launch selection requires an action and an item list")
    if len(item_refcodes) > 100:
        raise ValueError("A launch selection cannot contain more than 100 items")
    if any(not isinstance(refcode, str) for refcode in item_refcodes):
        raise ValueError("Selected item refcodes must be strings")

    ordered_refcodes = tuple(dict.fromkeys(item_refcodes))
    try:
        selection = ItemSelection(
            action_id=action_id,
            item_refcodes=ordered_refcodes,
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    action = next(
        (
            candidate
            for candidate in provider.metadata.launch_actions
            if candidate.id == selection.action_id
        ),
        None,
    )
    if action is None:
        raise ValueError("The requested launch action is not supported by this tool")
    if not action.min_items <= len(selection.item_refcodes) <= action.max_items:
        raise ValueError("The selected-item count is outside this tool action's limits")
    return selection


@TOOLS.route("/info/tools", methods=["GET"])
@active_users_or_get_only
def list_tools():
    """List tools enabled and available to the active current user."""
    context = _active_tool_context()
    if context is None:
        return jsonify({"error": "Unauthorized"}), 401

    response = JSONAPIResponse(
        data=[
            Data(
                id=provider.id,
                type="tool",
                attributes=Attributes(**provider.metadata.model_dump(mode="json")),
            )
            for provider in _registry().available_for(context)
        ],
        meta=Meta(query=request.query_string.decode() if request.query_string else ""),
    )
    catalog_response = jsonify(response.model_dump(mode="json"))
    catalog_response.headers["Cache-Control"] = "private, no-store"
    return catalog_response, 200


@TOOLS.route("/tools/<string:tool_id>/launch", methods=["POST"])
@active_users_or_get_only
def launch_tool(tool_id: str):
    """Prepare a tool launch for the active current user."""
    if not current_user.is_authenticated or not is_browser_session_user(current_user):
        return jsonify({"status": "error", "message": "A browser session is required"}), 403

    if not request_origin_is_allowed():
        return jsonify({"status": "error", "message": "Untrusted request origin"}), 403

    context = _active_tool_context()
    if context is None:
        return jsonify({"error": "Unauthorized"}), 401

    provider = _registry().available_provider(tool_id, context)
    if provider is None:
        return jsonify({"status": "error", "message": "Tool not found or unavailable"}), 404

    try:
        selection = _launch_selection(provider)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    issuer = BoundToolLaunchGrantIssuer(
        tool_id=tool_id,
        user_id=context.user_id,
        selection=selection,
    )
    try:
        result = provider.launch(context, issuer)
        launch_data = {}
        if isinstance(provider.metadata.ui, StandaloneToolUI):
            if not isinstance(result, str):
                raise TypeError("Standalone tool launches must return an HTTP(S) URL")
            launch_data["url"] = str(TypeAdapter(AnyHttpUrl).validate_python(result))
        elif result is not None:
            raise TypeError("In-app tool launches must return None")
    except Exception:
        LOGGER.exception("Unable to launch tool provider %r", tool_id)
        return jsonify({"status": "error", "message": "Unable to launch tool"}), 503

    response = jsonify(launch_data)
    response.headers["Cache-Control"] = "no-store"
    return response, 200


@TOOLS.route("/tools/<string:tool_id>/selection/exchange", methods=["POST"])
@active_users_or_get_only
def exchange_tool_selection(tool_id: str):
    """Consume a selected-items handoff from the authenticated delegated tool."""
    if not current_user.is_authenticated or not is_tool_access_token_user(current_user):
        return jsonify({"status": "error", "message": "A tool access token is required"}), 403

    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not isinstance(code, str) or not code:
        return jsonify({"status": "error", "message": "A selection code is required"}), 400

    tool_access_token = request.headers.get("DATALAB-API-KEY", "")
    selection = consume_tool_selection_code(
        code=code,
        tool_id=tool_id,
        tool_access_token=tool_access_token,
        expected_user_id=str(current_user.person.immutable_id),
    )
    if selection is None:
        return (
            jsonify({"status": "error", "message": "Invalid or expired selection code"}),
            400,
        )

    response = jsonify(
        {
            "action": selection.action_id,
            "items": list(selection.item_refcodes),
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response, 200
