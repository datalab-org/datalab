from types import SimpleNamespace

import pytest
from flask import Blueprint, Flask, current_app, request
from flask_login import LoginManager, UserMixin

from pydatalab.config import CONFIG
from pydatalab.login import AuthMethod
from pydatalab.models.people import AccountStatus
from pydatalab.models.utils import UserRole
from pydatalab.tools import StandaloneToolUI, ToolMetadata, ToolProvider, ToolRouteAuth
from pydatalab.tools import registry as registry_module
from pydatalab.tools.registry import ToolRegistry, create_tool_registry, register_tool_blueprints


@pytest.fixture(scope="module", autouse=True)
def insert_demo_users():
    """Keep these registry unit tests independent of the server's MongoDB fixtures."""


TEST_METADATA = ToolMetadata(
    name="Route test tool",
    description="A provider used to test tool route registration.",
    ui=StandaloneToolUI(),
)


def route_blueprint(name: str, *, nested: bool = False) -> Blueprint:
    parent = Blueprint(name, __name__)
    routes = Blueprint("nested", __name__) if nested else parent

    @routes.get("/route")
    def route():
        current_app.extensions["route_calls"][name] += 1
        return {"status": "ok"}

    if nested:
        parent.register_blueprint(routes)
    return parent


class NestedBrowserTool(ToolProvider):
    id = "nested-browser"
    metadata = TEST_METADATA
    blueprint = route_blueprint("nested-browser", nested=True)


class NestedServiceTool(ToolProvider):
    id = "nested-service"
    metadata = TEST_METADATA
    blueprint = route_blueprint("nested-service", nested=True)
    route_auth = ToolRouteAuth.SERVICE

    def is_available(self, context):
        raise AssertionError("Service routes must not evaluate browser availability")

    def authenticate_service_request(self) -> bool:
        return request.headers.get("X-Tool-Credential") == "valid"


class UnavailableBrowserTool(ToolProvider):
    id = "unavailable-browser"
    metadata = TEST_METADATA
    blueprint = route_blueprint("unavailable-browser")

    def is_available(self, context):
        return False


class AvailableBrowserTool(ToolProvider):
    id = "available-browser"
    metadata = TEST_METADATA
    blueprint = route_blueprint("available-browser")

    def is_available(self, context):
        assert context.user_id == "browser-route-user-id"
        assert context.group_ids == ("browser-route-group-id",)
        return True


class RaisingBrowserTool(ToolProvider):
    id = "raising-browser"
    metadata = TEST_METADATA
    blueprint = route_blueprint("raising-browser")

    def is_available(self, context):
        raise RuntimeError("availability failed")


class BrowserRouteTestUser(UserMixin):
    id = "browser-route-user"
    account_status = AccountStatus.ACTIVE
    auth_method = AuthMethod.BROWSER_SESSION
    display_name = "Browser Route User"
    role = UserRole.USER
    person = type("Person", (), {"immutable_id": "browser-route-user-id"})()
    groups = (type("Group", (), {"immutable_id": "browser-route-group-id"})(),)


@pytest.fixture
def tool_app(monkeypatch) -> Flask:
    monkeypatch.setattr(CONFIG, "ROOT_PATH", "/")
    monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", set())

    app = Flask(__name__)
    app.secret_key = "tool-registry-test-secret"  # noqa: S105
    app.extensions["route_calls"] = {
        "nested-browser": 0,
        "nested-service": 0,
        "unavailable-browser": 0,
        "available-browser": 0,
        "raising-browser": 0,
    }
    login_manager = LoginManager(app)
    browser_user = BrowserRouteTestUser()

    @login_manager.user_loader
    def load_user(user_id: str):
        return browser_user if user_id == browser_user.id else None

    registry = ToolRegistry()
    for provider in (
        NestedBrowserTool(),
        NestedServiceTool(),
        UnavailableBrowserTool(),
        AvailableBrowserTool(),
        RaisingBrowserTool(),
    ):
        registry.register(provider)
    register_tool_blueprints(app, registry)
    return app


def authenticated_client(app: Flask):
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = BrowserRouteTestUser.id
    return client


def test_discovery_honours_configured_tool_order(monkeypatch):
    entry_points = [
        SimpleNamespace(name="available-browser", load=lambda: AvailableBrowserTool),
        SimpleNamespace(name="nested-browser", load=lambda: NestedBrowserTool),
    ]
    monkeypatch.setattr(registry_module, "entry_points", lambda **_kwargs: entry_points)
    monkeypatch.setattr(CONFIG.TOOLS, "ORDER", ["nested-browser"])

    registry = create_tool_registry()

    assert [provider.id for provider in registry.providers] == [
        "nested-browser",
        "available-browser",
    ]


@pytest.mark.parametrize("api_prefix", ("", "/v0.1.0"))
def test_nested_routes_apply_browser_and_service_authentication(tool_app, api_prefix):
    client = tool_app.test_client()

    browser_response = client.get(f"{api_prefix}/tools/plugins/nested-browser/route")
    missing_service_credential = client.get(f"{api_prefix}/tools/plugins/nested-service/route")
    valid_service_credential = client.get(
        f"{api_prefix}/tools/plugins/nested-service/route",
        headers={"X-Tool-Credential": "valid"},
    )

    assert browser_response.status_code == 401
    assert browser_response.json["message"] == "Authentication required"
    assert missing_service_credential.status_code == 401
    assert missing_service_credential.json["message"] == "Invalid service credentials"
    assert valid_service_credential.status_code == 200
    assert valid_service_credential.json == {"status": "ok"}


def test_partially_registered_provider_routes_fail_closed(monkeypatch):
    monkeypatch.setattr(CONFIG, "ROOT_PATH", "/")
    monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", set())

    blueprint = Blueprint("partially_registered", __name__)

    @blueprint.get("/route")
    def partial_route():
        return {"status": "ok"}

    @blueprint.record
    def fail_registration(_state):
        raise RuntimeError("registration failed")

    class PartiallyRegisteredTool(ToolProvider):
        id = "partially-registered"
        metadata = TEST_METADATA

    PartiallyRegisteredTool.blueprint = blueprint

    app = Flask(__name__)
    registry = ToolRegistry()
    registry.register(PartiallyRegisteredTool())
    register_tool_blueprints(app, registry)

    route = "/tools/plugins/partially-registered/route"
    assert route in {rule.rule for rule in app.url_map.iter_rules()}
    assert app.test_client().get(route).status_code == 404


def test_unavailable_browser_route_requires_login_then_fails_closed(tool_app):
    route = "/tools/plugins/unavailable-browser/route"

    assert tool_app.test_client().get(route).status_code == 401
    response = authenticated_client(tool_app).get(route)

    assert response.status_code == 404
    assert response.json == {"status": "error", "message": "Tool not available"}
    assert tool_app.extensions["route_calls"]["unavailable-browser"] == 0


def test_browser_route_options_remains_exempt(tool_app):
    response = tool_app.test_client().options("/tools/plugins/unavailable-browser/route")

    assert response.status_code == 200
    assert tool_app.extensions["route_calls"]["unavailable-browser"] == 0


def test_available_browser_route_receives_current_user_context(tool_app):
    response = authenticated_client(tool_app).get("/tools/plugins/available-browser/route")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    assert tool_app.extensions["route_calls"]["available-browser"] == 1


def test_raising_availability_callback_fails_closed(tool_app):
    response = authenticated_client(tool_app).get("/tools/plugins/raising-browser/route")

    assert response.status_code == 404
    assert tool_app.extensions["route_calls"]["raising-browser"] == 0
