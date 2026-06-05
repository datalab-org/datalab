from unittest.mock import MagicMock

import os
import pytest

from pydatalab.main import create_app
from pydatalab.routes.v0_1 import auth as auth_routes
from pydatalab.errors import UserRegistrationForbidden
from pydatalab import config as datalab_config
from pydatalab.models.people import IdentityType


def test_unauthenticated_homepage_shows_login_buttons(unauthenticated_client):
    resp = unauthenticated_client.get("/")
    assert resp.status_code == 200
    assert b"Login via" in resp.data
    assert b"GitHub" in resp.data


def test_authenticated_homepage_shows_connect_buttons(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Connect GitHub" in resp.data


def test_homepage_does_not_crash_with_all_providers(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_homepage_hides_button_for_existing_identity(database, client, user_id):
    database.users.update_one(
        {"_id": user_id},
        {
            "$push": {
                "identities": {
                    "identity_type": "github",
                    "identifier": "12345",
                    "name": "octocat",
                    "verified": True,
                    "display_name": "The Octocat",
                }
            }
        },
    )

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Connect GitHub" not in resp.data


def test_forward_oauthlib_relax_flag_is_set(monkeypatch):
    cfg = {"OAUTHLIB_RELAX_TOKEN_SCOPE": "1"}
    app = create_app(config_override=cfg, env_file=False)
    assert os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE") == "1"


def test_microsoft_registration_blocks_disallowed_domain(monkeypatch, app):
    from pydatalab.routes.v0_1.auth import microsoft_logged_in

    monkeypatch.setattr(datalab_config.CONFIG, "EMAIL_DOMAIN_ALLOW_LIST", ["example.org"])

    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {
        "id": "ms-id-123",
        "mail": "user@notallowed.com",
        "displayName": "Bad User",
    }

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        with pytest.raises(UserRegistrationForbidden):
            microsoft_logged_in(fake_blueprint, token={"access_token": "fake"})


def test_enum_string_lookup_no_keyerror(app):
    # Ensure homepage doesn't KeyError when providers are enums
    monkey_cfg = {"OAUTH_PROXIES": [IdentityType.GOOGLE]}
    a = create_app(config_override=monkey_cfg, env_file=False)
    c = a.test_client()
    resp = c.get("/")
    assert resp.status_code == 200


def test_google_scope_canonicalization():
    # creating the blueprint should accept space/separated scope strings
    bp = auth_routes.make_google_blueprint(scope=["openid", "profile", "email"])
    assert hasattr(bp, "session")


def test_google_logged_in_handles_userinfo(monkeypatch, app):
    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {"id": "g-123", "email": "g@ex.com", "name": "GUsr"}

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    from pydatalab.routes.v0_1.auth import google_logged_in

    with app.test_request_context():
        # allow registration for test
        monkeypatch.setattr(datalab_config.CONFIG, "EMAIL_DOMAIN_ALLOW_LIST", None, raising=False)
        # should not raise KeyError or other unexpected exceptions
        google_logged_in(fake_blueprint, token={"access_token": "fake"})


def test_oauth_session_error_does_not_crash(monkeypatch, app):
    fake_resp = MagicMock()
    fake_resp.ok = False
    fake_resp.json.return_value = {}

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    from pydatalab.routes.v0_1.auth import google_logged_in

    with app.test_request_context():
        # handler should handle non-ok responses gracefully
        google_logged_in(fake_blueprint, token={"access_token": "fake"})


def test_connect_button_hidden_for_existing_google(database, client, user_id):
    database.users.update_one(
        {"_id": user_id},
        {
            "$push": {
                "identities": {
                    "identity_type": "google",
                    "identifier": "g-1",
                    "name": "guser",
                    "verified": True,
                    "display_name": "G User",
                }
            }
        },
    )
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Connect Google" not in resp.data


def test_provider_missing_from_connect_buttons_does_not_crash(app):
    cfg = {"OAUTH_PROXIES": ["nonexistent_provider"]}
    a = create_app(config_override=cfg, env_file=False)
    c = a.test_client()
    resp = c.get("/")
    assert resp.status_code == 200
