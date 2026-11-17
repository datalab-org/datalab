from datetime import datetime, timedelta, timezone

import pytest
from flask.testing import FlaskClient

from pydatalab.config import CONFIG
from pydatalab.login import AuthMethod, get_by_api_key, get_by_id
from pydatalab.models.utils import UserRole
from pydatalab.mongo import create_default_indices
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
    exchange_service_launch_code,
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


class OtherExampleTool(ExampleTool):
    id = "other-example-tool"
    metadata = ToolMetadata(
        name="Other example tool",
        description="Another test tool.",
        ui=StandaloneToolUI(),
    )


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


def test_delegated_tool_session_relaunch_replaces_only_same_user_and_provider(
    app,
    database,
    tool_registry,
    user_id,
    another_user_id,
):
    tool_registry.register(OtherExampleTool())

    with app.app_context():
        first = create_delegated_tool_session(str(user_id), "example-tool", "first-client")
        assert get_tool_access_token_user_id(first.tool_access_token) == str(user_id)

        legacy_session = database.tool_sessions.find_one(
            {"user": user_id, "tool_id": "example-tool"}
        )
        legacy_session.pop("_id")
        legacy_session["hash"] = "pre-upgrade-session-hash"
        database.tool_sessions.insert_one(legacy_session)
        assert (
            database.tool_sessions.count_documents({"user": user_id, "tool_id": "example-tool"})
            == 2
        )

        second = create_delegated_tool_session(str(user_id), "example-tool", "first-client")
        assert get_tool_access_token_user_id(first.tool_access_token) is None
        assert get_tool_access_token_user_id(second.tool_access_token) == str(user_id)
        assert (
            database.tool_sessions.count_documents(
                {"user": user_id, "tool_id": "example-tool", "type": "tool_access_token"}
            )
            == 1
        )

        different_client = create_delegated_tool_session(
            str(user_id), "example-tool", "second-client"
        )
        assert get_tool_access_token_user_id(second.tool_access_token) is None
        assert get_tool_access_token_user_id(different_client.tool_access_token) == str(user_id)
        assert (
            database.tool_sessions.find_one({"user": user_id, "tool_id": "example-tool"})[
                "client_id"
            ]
            == "second-client"
        )

        other_user = create_delegated_tool_session(
            str(another_user_id), "example-tool", "first-client"
        )
        other_tool = create_delegated_tool_session(
            str(user_id), "other-example-tool", "first-client"
        )

        assert get_tool_access_token_user_id(different_client.tool_access_token) == str(user_id)
        assert get_tool_access_token_user_id(other_user.tool_access_token) == str(another_user_id)
        assert get_tool_access_token_user_id(other_tool.tool_access_token) == str(user_id)
        assert database.tool_sessions.count_documents({}) == 3


def test_tool_session_indexes(real_mongo_client):
    create_default_indices(real_mongo_client)
    indexes = real_mongo_client.get_database().tool_sessions.index_information()

    hash_index = indexes["unique delegated tool session hash"]
    assert hash_index["key"] == [("hash", 1)]
    assert hash_index["unique"] is True
    assert indexes["delegated tool session owner and provider"]["key"] == [
        ("user", 1),
        ("tool_id", 1),
        ("type", 1),
    ]


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
        exchange = exchange_launch_code(
            launch_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )

        assert exchange is not None
        assert exchange.context.user_id == str(user_id)
        assert exchange.selection == selection
        assert (
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id=str(user_id),
            )
            is None
        )

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


def test_launch_exchange_requires_browser_user_binding(
    app,
    user_id,
    admin_user_id,
    tool_registry,
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
        )
        launch_code = issuer.issue("example-client")

        with pytest.raises(TypeError, match="expected_user_id"):
            exchange_launch_code(launch_code, "example-tool", "example-client")
        with pytest.raises(ValueError, match="must not be empty"):
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id="",
            )
        with pytest.raises(ValueError, match="must not be empty"):
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id=None,
            )

        assert (
            exchange_launch_code(
                launch_code,
                "example-tool",
                "example-client",
                expected_user_id=str(admin_user_id),
            )
            is None
        )
        exchange = exchange_launch_code(
            launch_code,
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None
        assert exchange.context.user_id == str(user_id)

        service_exchange = exchange_service_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
        )
        assert service_exchange is not None
        assert service_exchange.context.user_id == str(user_id)


def test_admin_tool_token_uses_restricted_effective_role(
    app,
    admin_user_id,
    admin_api_key,
    tool_registry,
):
    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(admin_user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(admin_user_id),
        )

        assert exchange is not None
        assert exchange.context.role == "user"

        delegated_user = get_by_api_key(exchange.tool_session.tool_access_token)
        assert delegated_user is not None
        assert delegated_user.auth_method is AuthMethod.TOOL_ACCESS_TOKEN
        assert delegated_user.role is UserRole.USER

        delegated_user.refresh()
        assert delegated_user.auth_method is AuthMethod.TOOL_ACCESS_TOKEN
        assert delegated_user.role is UserRole.USER

        browser_user = get_by_id(admin_user_id)
        assert browser_user is not None
        assert browser_user.auth_method is AuthMethod.BROWSER_SESSION
        assert browser_user.role is UserRole.ADMIN
        browser_user.refresh()
        assert browser_user.auth_method is AuthMethod.BROWSER_SESSION
        assert browser_user.role is UserRole.ADMIN

        api_key_user = get_by_api_key(admin_api_key)
        assert api_key_user is not None
        assert api_key_user.auth_method is AuthMethod.PERMANENT_API_KEY
        assert api_key_user.role is UserRole.ADMIN
        api_key_user.refresh()
        assert api_key_user.auth_method is AuthMethod.PERMANENT_API_KEY
        assert api_key_user.role is UserRole.ADMIN

    app.test_client_class = FlaskClient
    response = app.test_client().get(
        "/get-current-user/",
        headers={"DATALAB-API-KEY": exchange.tool_session.tool_access_token},
    )
    assert response.status_code == 200
    assert response.json["role"] == "user"


def test_admin_tool_token_has_no_implicit_admin_permissions(
    app,
    client,
    admin_user_id,
    tool_registry,
):
    response = client.post(
        "/new-sample/",
        json={"type": "samples", "item_id": "admin-tool-token-private-sample"},
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(admin_user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(admin_user_id),
        )
        assert exchange is not None

    tool_headers = {"DATALAB-API-KEY": exchange.tool_session.tool_access_token}
    app.test_client_class = FlaskClient
    tool_client = app.test_client()

    response = tool_client.get(f"/items/{refcode}?sudo=1", headers=tool_headers)
    assert response.status_code == 404

    response = tool_client.patch(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(admin_user_id)}]},
        headers=tool_headers,
    )
    assert response.status_code == 401

    response = tool_client.put(
        "/tags",
        json={"data": {"name": "admin-tool-token-global", "scope": "global"}},
        headers=tool_headers,
    )
    assert response.status_code == 403


def test_tool_token_cannot_issue_item_access_token(
    app,
    client,
    database,
    tool_registry,
    user_id,
):
    response = client.post(
        "/new-sample/",
        json={"type": "samples", "item_id": "tool-token-owned-sample"},
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    with app.app_context():
        issuer = BoundToolLaunchGrantIssuer(
            tool_id="example-tool",
            user_id=str(user_id),
        )
        exchange = exchange_launch_code(
            issuer.issue("example-client"),
            "example-tool",
            "example-client",
            expected_user_id=str(user_id),
        )
        assert exchange is not None

    item_token_query = {"type": "access_token", "refcode": refcode}
    token_count = database.api_keys.count_documents(item_token_query)

    app.test_client_class = FlaskClient
    response = app.test_client().post(
        f"/items/{refcode}/issue-access-token",
        headers={"DATALAB-API-KEY": exchange.tool_session.tool_access_token},
    )

    assert response.status_code == 403
    assert response.json == {
        "title": "Forbidden",
        "message": (
            "A tool's temporary access cannot be used to create long-lived access to an item."
        ),
        "status": "error",
    }
    assert database.api_keys.count_documents(item_token_query) == token_count


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


@pytest.mark.parametrize(
    "launch_url",
    (
        "https://tools.example.test/start",
        "http://localhost:8080/start",
        "http://a.localhost/start",
        "http://127.0.0.1/start",
        "http://127.42.0.9/start",
        "http://[::1]:8080/start",
    ),
)
def test_tool_launch_accepts_https_and_loopback_http(
    session_client, tool_registry, monkeypatch, launch_url
):
    monkeypatch.setattr(ExampleTool, "launch", lambda self, context, grants: launch_url)

    response = session_client.post(
        "/tools/example-tool/launch",
        json={},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 200
    assert response.json["url"] == launch_url


@pytest.mark.parametrize(
    "launch_result",
    (
        "http://tools.example.test/start?code=must-not-leak",
        "http://192.168.1.20/start",
        "http://localhost.example.com/start",
        "https://user:secret@tools.example.test/start",
        "http://user:secret@localhost/start",
        "ftp://tools.example.test/start",
        None,
    ),
)
def test_tool_launch_rejects_unsafe_urls_without_disclosure(
    session_client, tool_registry, monkeypatch, launch_result
):
    monkeypatch.setattr(ExampleTool, "launch", lambda self, context, grants: launch_result)

    response = session_client.post(
        "/tools/example-tool/launch",
        json={},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 503
    assert response.json == {"status": "error", "message": "Unable to launch tool"}
    assert "must-not-leak" not in response.get_data(as_text=True)


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
