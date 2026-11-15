import pytest
from flask import Blueprint, Flask, request
from flask_login import LoginManager

from pydatalab.config import CONFIG
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
