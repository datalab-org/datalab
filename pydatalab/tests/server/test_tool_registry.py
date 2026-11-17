import pytest
from flask import Blueprint, Flask, request
from flask_login import LoginManager, UserMixin

from pydatalab.config import CONFIG
from pydatalab.login import AuthMethod
from pydatalab.models.people import AccountStatus
from pydatalab.models.utils import UserRole
from pydatalab.tools import StandaloneToolUI, ToolMetadata, ToolProvider, ToolRouteAuth
from pydatalab.tools.registry import ToolRegistry, register_tool_blueprints


@pytest.fixture(scope="module", autouse=True)
def insert_demo_users():
    """Keep these registry unit tests independent of the server's MongoDB fixtures."""


def nested_blueprint(name: str) -> Blueprint:
    parent = Blueprint(name, __name__)
    child = Blueprint("nested", __name__)

    @child.get("/route")
    def nested_route():
        return {"status": "ok"}

    parent.register_blueprint(child)
    return parent


class NestedBrowserTool(ToolProvider):
    id = "nested-browser"
    metadata = ToolMetadata(
        name="Nested browser tool",
        description="A nested browser-authenticated test tool.",
        ui=StandaloneToolUI(),
    )
    blueprint = nested_blueprint("nested_browser")


class NestedServiceTool(ToolProvider):
    id = "nested-service"
    metadata = ToolMetadata(
        name="Nested service tool",
        description="A nested service-authenticated test tool.",
        ui=StandaloneToolUI(),
    )
    blueprint = nested_blueprint("nested_service")
    route_auth = ToolRouteAuth.SERVICE

    def authenticate_service_request(self) -> bool:
        return request.headers.get("X-Tool-Credential") == "valid"


@pytest.fixture
def nested_tool_app(monkeypatch) -> Flask:
    monkeypatch.setattr(CONFIG, "ROOT_PATH", "/")
    monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", set())

    app = Flask(__name__)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(_user_id: str):
        return None

    registry = ToolRegistry()
    registry.register(NestedBrowserTool())
    registry.register(NestedServiceTool())
    register_tool_blueprints(app, registry)
    return app


@pytest.mark.parametrize("api_prefix", ("", "/v0", "/v0.1", "/v0.1.0"))
def test_nested_provider_routes_inherit_authentication(nested_tool_app, api_prefix):
    with nested_tool_app.test_client() as client:
        browser_response = client.get(f"{api_prefix}/tools/plugins/nested-browser/route")
        missing_service_credential = client.get(f"{api_prefix}/tools/plugins/nested-service/route")
        invalid_service_credential = client.get(
            f"{api_prefix}/tools/plugins/nested-service/route",
            headers={"X-Tool-Credential": "invalid"},
        )
        valid_service_credential = client.get(
            f"{api_prefix}/tools/plugins/nested-service/route",
            headers={"X-Tool-Credential": "valid"},
        )

    assert browser_response.status_code == 401
    assert browser_response.json["message"] == "Authentication required"
    assert missing_service_credential.status_code == 401
    assert missing_service_credential.json["message"] == "Invalid service credentials"
    assert invalid_service_credential.status_code == 401
    assert invalid_service_credential.json["message"] == "Invalid service credentials"
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
        metadata = ToolMetadata(
            name="Partially registered tool",
            description="A tool that fails after installing its first route.",
            ui=StandaloneToolUI(),
        )

    PartiallyRegisteredTool.blueprint = blueprint

    app = Flask(__name__)
    registry = ToolRegistry()
    provider = PartiallyRegisteredTool()
    registry.register(provider)
    register_tool_blueprints(app, registry)

    route = "/tools/plugins/partially-registered/route"
    assert registry.get(provider.id) is None
    assert route in {rule.rule for rule in app.url_map.iter_rules()}

    with app.test_client() as client:
        response = client.get(route)

    assert response.status_code == 404
    assert response.json == {"status": "error", "message": "Tool not available"}


class BrowserRouteTestUser(UserMixin):
    id = "browser-route-user"
    account_status = AccountStatus.ACTIVE
    auth_method = AuthMethod.BROWSER_SESSION
    display_name = "Browser Route User"
    role = UserRole.USER
    person = type("Person", (), {"immutable_id": "browser-route-user-id"})()
    groups = (type("Group", (), {"immutable_id": "browser-route-group-id"})(),)


@pytest.fixture
def availability_tool_app(monkeypatch) -> Flask:
    monkeypatch.setattr(CONFIG, "ROOT_PATH", "/")
    monkeypatch.setattr(CONFIG.TOOLS, "DISABLED", set())

    route_calls = {"unavailable": 0, "available": 0, "raising": 0, "service": 0}

    unavailable_blueprint = Blueprint("unavailable_browser", __name__)
    unavailable_nested_blueprint = Blueprint("nested", __name__)

    @unavailable_blueprint.get("/flat")
    def unavailable_flat_route():
        route_calls["unavailable"] += 1
        return {"status": "ok"}

    @unavailable_nested_blueprint.get("/nested")
    def unavailable_nested_route():
        route_calls["unavailable"] += 1
        return {"status": "ok"}

    unavailable_blueprint.register_blueprint(unavailable_nested_blueprint)

    available_blueprint = Blueprint("available_browser", __name__)

    @available_blueprint.get("/route")
    def available_route():
        route_calls["available"] += 1
        return {"status": "ok"}

    raising_blueprint = Blueprint("raising_browser", __name__)

    @raising_blueprint.get("/route")
    def raising_route():
        route_calls["raising"] += 1
        return {"status": "ok"}

    service_blueprint = Blueprint("unavailable_service", __name__)

    @service_blueprint.get("/route")
    def service_route():
        route_calls["service"] += 1
        return {"status": "ok"}

    class UnavailableBrowserTool(ToolProvider):
        id = "unavailable-browser"
        metadata = ToolMetadata(
            name="Unavailable browser tool",
            description="A browser tool unavailable to the current user.",
            ui=StandaloneToolUI(),
        )
        blueprint = unavailable_blueprint

        def is_available(self, context):
            return False

    class AvailableBrowserTool(ToolProvider):
        id = "available-browser"
        metadata = ToolMetadata(
            name="Available browser tool",
            description="A browser tool available to the current user.",
            ui=StandaloneToolUI(),
        )
        blueprint = available_blueprint

        def is_available(self, context):
            assert context.user_id == "browser-route-user-id"
            assert context.display_name == "Browser Route User"
            assert context.role == "user"
            assert context.group_ids == ("browser-route-group-id",)
            return True

    class RaisingBrowserTool(ToolProvider):
        id = "raising-browser"
        metadata = ToolMetadata(
            name="Raising browser tool",
            description="A browser tool with a broken availability callback.",
            ui=StandaloneToolUI(),
        )
        blueprint = raising_blueprint

        def is_available(self, context):
            raise RuntimeError("availability failed")

    class UnavailableServiceTool(ToolProvider):
        id = "unavailable-service"
        metadata = ToolMetadata(
            name="Unavailable service tool",
            description="A service tool whose browser availability is irrelevant.",
            ui=StandaloneToolUI(),
        )
        blueprint = service_blueprint
        route_auth = ToolRouteAuth.SERVICE

        def is_available(self, context):
            raise AssertionError("Service routes must not evaluate browser availability")

        def authenticate_service_request(self) -> bool:
            return request.headers.get("X-Tool-Credential") == "valid"

    app = Flask(__name__)
    app.secret_key = "tool-registry-test-secret"  # noqa: S105
    login_manager = LoginManager(app)
    browser_user = BrowserRouteTestUser()

    @login_manager.user_loader
    def load_user(user_id: str):
        return browser_user if user_id == browser_user.id else None

    registry = ToolRegistry()
    registry.register(UnavailableBrowserTool())
    registry.register(AvailableBrowserTool())
    registry.register(RaisingBrowserTool())
    registry.register(UnavailableServiceTool())
    register_tool_blueprints(app, registry)
    app.extensions["route_calls"] = route_calls
    return app


def authenticated_client(app: Flask):
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = BrowserRouteTestUser.id
    return client


@pytest.mark.parametrize("api_prefix", ("", "/v0", "/v0.1", "/v0.1.0"))
@pytest.mark.parametrize("route", ("flat", "nested"))
def test_unavailable_browser_provider_routes_fail_closed(
    availability_tool_app,
    api_prefix,
    route,
):
    client = authenticated_client(availability_tool_app)

    response = client.get(f"{api_prefix}/tools/plugins/unavailable-browser/{route}")

    assert response.status_code == 404
    assert response.json == {"status": "error", "message": "Tool not available"}
    assert availability_tool_app.extensions["route_calls"]["unavailable"] == 0


def test_unavailable_browser_provider_route_still_requires_authentication(
    availability_tool_app,
):
    response = availability_tool_app.test_client().get("/tools/plugins/unavailable-browser/flat")

    assert response.status_code == 401
    assert response.json == {"status": "error", "message": "Authentication required"}
    assert availability_tool_app.extensions["route_calls"]["unavailable"] == 0


@pytest.mark.parametrize("api_prefix", ("", "/v0", "/v0.1", "/v0.1.0"))
def test_unavailable_browser_provider_options_remains_exempt(
    availability_tool_app,
    api_prefix,
):
    response = availability_tool_app.test_client().options(
        f"{api_prefix}/tools/plugins/unavailable-browser/flat"
    )

    assert response.status_code == 200
    assert availability_tool_app.extensions["route_calls"]["unavailable"] == 0


def test_available_browser_provider_route_reaches_handler(availability_tool_app):
    response = authenticated_client(availability_tool_app).get(
        "/tools/plugins/available-browser/route"
    )

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    assert availability_tool_app.extensions["route_calls"]["available"] == 1


def test_raising_browser_provider_availability_fails_closed(availability_tool_app):
    response = authenticated_client(availability_tool_app).get(
        "/tools/plugins/raising-browser/route"
    )

    assert response.status_code == 404
    assert response.json == {"status": "error", "message": "Tool not available"}
    assert availability_tool_app.extensions["route_calls"]["raising"] == 0


def test_service_provider_route_does_not_use_browser_availability(availability_tool_app):
    response = availability_tool_app.test_client().get(
        "/tools/plugins/unavailable-service/route",
        headers={"X-Tool-Credential": "valid"},
    )

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    assert availability_tool_app.extensions["route_calls"]["service"] == 1
