from datetime import datetime, timedelta, timezone

import pytest
from flask.testing import FlaskClient

from pydatalab.config import CONFIG
from pydatalab.permissions import get_default_permissions
from pydatalab.tools import (
    ItemSelection,
    ItemTableSelectionAction,
    StandaloneToolUI,
    ToolContext,
    ToolMetadata,
    ToolProvider,
)
from pydatalab.tools.grants import (
    BoundToolLaunchGrantIssuer,
    consume_tool_selection_code,
    create_delegated_tool_session,
    exchange_launch_code,
    get_tool_access_token_user_id,
    issue_tool_selection_code,
)
from pydatalab.tools.registry import TOOL_REGISTRY_EXTENSION, ToolRegistry


class ExampleTool(ToolProvider):
    id = "example-tool"
    metadata = ToolMetadata(
        name="Example tool",
        description="A test tool.",
        ui=StandaloneToolUI(),
        launch_actions=(
            ItemTableSelectionAction(
                id="compare-items",
                label="Compare items",
                tables=("samples",),
                min_items=2,
                max_items=3,
            ),
        ),
    )

    def launch(self, context, grants):
        code = grants.issue("example-client")
        return f"https://tools.example.test/start?code={code}"


@pytest.fixture
def tool_registry(app):
    previous = app.extensions[TOOL_REGISTRY_EXTENSION]
    registry = ToolRegistry()
    registry.register(ExampleTool())
    app.extensions[TOOL_REGISTRY_EXTENSION] = registry
    yield registry
    app.extensions[TOOL_REGISTRY_EXTENSION] = previous


@pytest.fixture(autouse=True)
def clean_tool_credentials(database):
    database.tool_launch_grants.delete_many({})
    database.tool_sessions.delete_many({})
    yield
    database.tool_launch_grants.delete_many({})
    database.tool_sessions.delete_many({})


def test_registry_validation_and_availability(tool_registry):
    context = ToolContext(user_id="user", display_name="User", role="user", group_ids=())

    assert tool_registry.available_for(context) == [tool_registry.get("example-tool")]
    with pytest.raises(ValueError, match="Duplicate tool provider"):
        tool_registry.register(ExampleTool())


def test_delegated_tool_token_uses_key_fields_and_is_isolated(
    app, database, tool_registry, user_id
):
    with app.app_context():
        session = create_delegated_tool_session(str(user_id), "example-tool", "example-client")
        stored = database.tool_sessions.find_one({"tool_id": "example-tool"})

        assert stored["user"] == user_id
        assert stored["client_id"] == "example-client"
        assert stored["type"] == "tool_access_token"
        assert stored["version"] == 1
        assert isinstance(stored["hash"], str)
        assert stored["created_at"] <= stored["expires_at"]
        assert database.api_keys.find_one({"type": "tool_access_token"}) is None
        assert get_tool_access_token_user_id(session.tool_access_token) == str(user_id)

        database.tool_sessions.update_one(
            {"_id": stored["_id"]},
            {"$set": {"expires_at": datetime.now(tz=timezone.utc) - timedelta(seconds=1)}},
        )
        assert get_tool_access_token_user_id(session.tool_access_token) is None


def test_launch_and_selection_grants_are_single_use(app, user_id, tool_registry):
    selection = ItemSelection(
        action_id="compare-items",
        item_refcodes=("test:one", "test:two"),
    )

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
            selection=selection,
        )
        launch_code = issuer.issue("example-client")
        exchange = exchange_launch_code(launch_code, "example-tool", "example-client")

        assert exchange is not None
        assert exchange.context.user_id == str(user_id)
        assert exchange.selection == selection
        assert exchange_launch_code(launch_code, "example-tool", "example-client") is None

        selection_code = issue_tool_selection_code(
            user_id=str(user_id),
            tool_id="example-tool",
            selection=selection,
        )
        consumed = consume_tool_selection_code(
            code=selection_code,
            tool_id="example-tool",
            tool_access_token=exchange.tool_session.tool_access_token,
            expected_user_id=str(user_id),
        )
        assert consumed == selection
        assert (
            consume_tool_selection_code(
                code=selection_code,
                tool_id="example-tool",
                tool_access_token=exchange.tool_session.tool_access_token,
                expected_user_id=str(user_id),
            )
            is None
        )


def test_tool_catalog_and_launch_use_browser_session(session_client, tool_registry):
    catalog = session_client.get("/info/tools")

    assert catalog.status_code == 200
    assert catalog.headers["Cache-Control"] == "private, no-store"
    assert catalog.json["data"][0]["id"] == "example-tool"

    launch = session_client.post(
        "/tools/example-tool/launch",
        json={"action": "compare-items", "items": ["test:one", "test:two"]},
        headers={"Origin": "http://localhost"},
    )

    assert launch.status_code == 200
    assert launch.json["url"].startswith("https://tools.example.test/start?code=")


def test_tool_launch_uses_read_permissions_for_administrators(
    app, admin_user_id, tool_registry, monkeypatch
):
    observed_permissions = []

    def launch_with_permission_probe(self, context, grants):
        observed_permissions.append(
            get_default_permissions(user_only=False, inherit_from_collections=False)
        )
        return "https://tools.example.test/start"

    monkeypatch.setattr(ExampleTool, "launch", launch_with_permission_probe)

    app.test_client_class = FlaskClient
    with app.test_client() as admin_session_client:
        with admin_session_client.session_transaction() as session:
            session["_user_id"] = str(admin_user_id)

        response = admin_session_client.post(
            "/tools/example-tool/launch",
            json={},
            headers={"Origin": "http://localhost"},
        )
        assert response.status_code == 200
        assert observed_permissions[-1] != {}

        response = admin_session_client.post(
            "/tools/example-tool/launch?sudo=1",
            json={},
            headers={"Origin": "http://localhost"},
        )
        assert response.status_code == 200
        assert observed_permissions[-1] == {}


def test_tool_launch_rejects_api_keys_and_invalid_selections(client, session_client, tool_registry):
    assert client.post("/tools/example-tool/launch", json={}).status_code == 403

    response = session_client.post(
        "/tools/example-tool/launch",
        json={"action": "compare-items", "items": ["test:one"]},
        headers={"Origin": "http://localhost"},
    )
    assert response.status_code == 400
    assert "outside this tool action's limits" in response.json["message"]


def test_disabling_tool_invalidates_delegated_token(
    app, database, tool_registry, user_id, monkeypatch
):
    with app.app_context():
        session = create_delegated_tool_session(str(user_id), "example-tool", "example-client")
        monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", {"example-tool"})
        assert get_tool_access_token_user_id(session.tool_access_token) is None
