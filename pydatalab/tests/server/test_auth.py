from unittest.mock import MagicMock

from bson import ObjectId

from pydatalab.routes.v0_1.auth import _check_email_domain


def test_allow_emails():
    # Test that a valid email is allowed
    assert _check_email_domain("test@example.org", ["example.org"])
    assert _check_email_domain("test@example.org", ["example.org", "example2.org"])
    assert _check_email_domain("test@subdomain.example.org", ["example.org", "example2.org"])
    assert _check_email_domain("test@subdomain.example.org", ["subdomain.example.org"])
    assert not _check_email_domain("test@example2.org", [])
    assert _check_email_domain("test@example2.org", None)
    assert not _check_email_domain("test@example.org", ["subdomain.example.org"])
    assert not _check_email_domain("test@example2.org", ["example.org"])


def test_magic_link_account_creation(unauthenticated_client, app, database):
    with app.extensions["mail"].record_messages() as outbox:
        response = unauthenticated_client.post(
            "/login/magic-link",
            json={"email": "test@ml-evs.science", "referrer": "datalab.example.org"},
        )
        assert response.json["message"] == "Email sent successfully."
        assert response.status_code == 200
        assert len(outbox) == 1

    doc = database.magic_links.find_one()
    assert "jwt" in doc

    with app.extensions["mail"].record_messages() as outbox:
        response = unauthenticated_client.get(f"/login/email?token={doc['jwt']}")
        assert response.status_code == 307
        new_user = database.users.find_one({"contact_email": "test@ml-evs.science"})
        assert new_user
        assert new_user["account_status"] == "unverified"
        assert len(outbox) == 1  # Should be a notification to admins


def test_magic_links_expected_failures(unauthenticated_client, app):
    with app.extensions["mail"].record_messages() as outbox:
        response = unauthenticated_client.post(
            "/login/magic-link",
            json={"email": "test@ml-evs.science"},
        )
        assert response.status_code == 400
        assert len(outbox) == 0

        response = unauthenticated_client.post(
            "/login/magic-link",
            json={"email": "not_an_email", "referrer": "datalab.example.org"},
        )
        assert response.status_code == 400
        assert len(outbox) == 0
        assert response.json["message"] == "Invalid email provided."

        response = unauthenticated_client.post(
            "/login/magic-link",
            json={"email": "banned_email@gmail.com", "referrer": "datalab.example.org"},
        )
        assert response.status_code == 403
        assert len(outbox) == 0


def test_magic_link_auth_can_be_disabled(unauthenticated_client, app, database, monkeypatch):
    from pydatalab import config

    monkeypatch.setattr(config.CONFIG, "DISABLE_MAGIC_LINK_AUTH", True)
    database.magic_links.delete_many({})

    with app.extensions["mail"].record_messages() as outbox:
        response = unauthenticated_client.post(
            "/login/magic-link",
            json={"email": "test@ml-evs.science", "referrer": "datalab.example.org"},
        )
        assert response.status_code == 403
        assert (
            response.json["message"]
            == "Magic-link authentication is disabled for this datalab instance."
        )
        assert len(outbox) == 0
        assert database.magic_links.count_documents({}) == 0

        response = unauthenticated_client.get("/login/email?token=unused")
        assert response.status_code == 403
        assert (
            response.json["message"]
            == "Magic-link authentication is disabled for this datalab instance."
        )
        assert len(outbox) == 0


# ──────────────────────────────────────────────
# API key tests
# ──────────────────────────────────────────────


def test_create_api_key(client, api_keys_db):
    json = {"name": "Test_API_KEY"}
    request_result = client.post("/api-keys", json=json)

    assert request_result.status_code == 200

    result_from_database = api_keys_db.find_one({"name": "Test_API_KEY"})

    assert result_from_database is not None
    assert result_from_database["digest"][4:-4] == "..."
    # delete_test_gen_api_keys(database, ["Test_API_KEY"])


def test_create_api_key_unauthorized(unauthenticated_client, api_keys_db):
    json = {"name": "Test_API_KEY"}
    request_result = unauthenticated_client.post("/api-keys", json=json)

    assert request_result.status_code == 401

    result_from_database = api_keys_db.find_one({"name": "Test_API_KEY"})
    assert result_from_database is None


def test_get_api_keys_for_user(client, api_keys_db, user_id):
    api_keys = [
        {
            "name": "Test_API_KEY_1",
            "digest": "234...567",
            "hash": "test hash",
            "user_id": str(user_id),
        },
        {
            "name": "Test_API_KEY_2",
            "digest": "658...098",
            "hash": "test hash",
            "user_id": str(user_id),
        },
        {
            "name": "Anaconda_instance_4",
            "digest": "433...851",
            "hash": "test hash",
            "user_id": str(user_id),
        },
    ]
    db_result = api_keys_db.insert_many(api_keys)
    assert len(db_result.inserted_ids) == 3

    request_result = client.get("/api-keys")
    assert request_result.status_code == 200
    request_json = list(request_result.json["api_keys"])

    assert len(request_json) == 4

    # First one will be the API key for the test client
    assert request_json[0]["name"] == "testing API key"

    assert request_json[1]["name"] == "Test_API_KEY_1"
    assert request_json[1]["digest"] == "234...567"
    assert request_json[1].get("hash", None) is None

    assert request_json[2]["name"] == "Test_API_KEY_2"
    assert request_json[2]["digest"] == "658...098"
    assert request_json[2].get("hash", None) is None

    assert request_json[3]["name"] == "Anaconda_instance_4"
    assert request_json[3]["digest"] == "433...851"
    assert request_json[3].get("hash", None) is None


def test_cannot_gain_access_to_unauthorised_api_keys(client, another_user_id, api_keys_db):
    api_keys = [
        {
            "name": "Test_API_KEY_1",
            "digest": "234...567",
            "hash": "test hash",
            "user_id": str(another_user_id),
        },
        {
            "name": "Test_API_KEY_2",
            "digest": "658...098",
            "hash": "test hash",
            "user_id": str(another_user_id),
        },
        {
            "name": "Anaconda_instance_4",
            "digest": "433...851",
            "hash": "test hash",
            "user_id": str(another_user_id),
        },
    ]
    db_result = api_keys_db.insert_many(api_keys)
    assert len(db_result.inserted_ids) == 3

    request_result = client.get("/api-keys")
    assert request_result.status_code == 200
    request_json = list(request_result.json["api_keys"])
    print(request_json)

    assert len(request_json) == 1

    # First one will be the API key for the test client
    assert request_json[0]["name"] == "testing API key"


def test_cannot_gain_authorised_access_to_api_keys(unauthenticated_client):
    request_result = unauthenticated_client.get("/api-keys")
    assert request_result.status_code == 401


def test_can_delete_api_key(client, api_keys_db, user_id):
    api_keys_db.insert_one(
        {
            "_id": ObjectId("507f1f88bcf86cd733439011"),
            "name": "Test_API_KEY_1",
            "digest": "234...567",
            "user_id": str(user_id),
        }
    )

    request_result = client.delete("/api-keys/507f1f88bcf86cd733439011")
    assert request_result.status_code == 204

    result = api_keys_db.find_one({"name": "Test_API_KEY_1", "digest": "234...567"})
    assert result is None


def test_cannot_delete_someone_else_api_key(client, another_user_id, api_keys_db):
    api_keys_db.insert_one(
        {
            "_id": ObjectId("507f1f88bcf86cd733439011"),
            "name": "Test_API_KEY_1",
            "digest": "234...567",
            "user_id": str(another_user_id),
        }
    )

    request_result = client.delete("/api-keys/507f1f88bcf86cd733439011")
    assert request_result.status_code == 404

    result = api_keys_db.find_one({"name": "Test_API_KEY_1", "digest": "234...567"})
    assert result is not None


def test_cannot_delete_api_key_when_unauthorised(unauthenticated_client, user_id, api_keys_db):
    api_keys_db.insert_one(
        {
            "_id": ObjectId("507f1f88bcf86cd733439011"),
            "name": "Test_API_KEY_1",
            "digest": "234...567",
            "user_id": str(user_id),
        }
    )

    request_result = unauthenticated_client.delete("/api-keys/507f1f88bcf86cd733439011")
    assert request_result.status_code == 401

    result = api_keys_db.find_one({"name": "Test_API_KEY_1", "digest": "234...567"})
    assert result is not None


# Legacy key tests ======================================
def test_retrieve_legacy_key(client, user_id, api_keys_db):
    # Create legacy API key
    api_keys_db.insert_one(
        {
            "_id": ObjectId(str(user_id)),
            "hash": "test hash",
        }
    )
    request_result = client.get("/api-keys")
    assert request_result.status_code == 200
    request_json = list(request_result.json["api_keys"])
    assert len(request_json) == 2
    assert request_json[0]["name"] == "Legacy key"
    assert request_json[0]["digest"] == "Unknown"


def test_delete_legacy_key(client, api_keys_db, user_id):
    api_keys_db.insert_one(
        {
            "_id": ObjectId(user_id),
            "hash": "test hash",
        }
    )
    request_result = client.delete(f"/api-keys/{user_id}")
    assert request_result.status_code == 204
    assert api_keys_db.find_one({"_id": ObjectId(user_id)}) is None


# ──────────────────────────────────────────────
# GitHub OAuth tests
# ──────────────────────────────────────────────


def test_github_login_success(database, app, monkeypatch):
    """A valid GitHub OAuth callback should create a new user in the database."""
    from pydatalab import config
    from pydatalab.routes.v0_1.auth import github_logged_in

    # Allow all GitHub users to register (no org restriction)
    monkeypatch.setattr(config.CONFIG, "GITHUB_ORG_ALLOW_LIST", None)

    # Simulate a successful response from the GitHub API
    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {
        "id": 12345,
        "login": "octocat",
        "name": "The Octocat",
    }

    # Simulate the Flask-Dance blueprint that calls GitHub on our behalf
    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        github_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    user = database.users.find_one({"identities.identifier": "12345"})
    assert user is not None
    assert user["display_name"] == "The Octocat"


def test_github_login_no_token(database, app):
    """If no OAuth token is provided, no user should be created."""
    database.users.delete_many({})
    from pydatalab.routes.v0_1.auth import github_logged_in

    fake_blueprint = MagicMock()

    with app.test_request_context():
        result = github_logged_in(fake_blueprint, token=None)

    assert result is False
    # Check that no GitHub user was created specifically
    assert database.users.find_one({"identities.identity_type": "github"}) is None


def test_github_login_bad_api_response(database, app):
    """If the GitHub API returns an error, no user should be created."""
    from pydatalab.routes.v0_1.auth import github_logged_in

    fake_resp = MagicMock()
    fake_resp.ok = False  # GitHub API failed

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        result = github_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    assert result is False
    assert database.users.find_one({"identities.identity_type": "github"}) is None


# ──────────────────────────────────────────────
# Google OAuth tests
# ──────────────────────────────────────────────


def test_google_login_success(database, app, monkeypatch):
    """A valid Google OAuth callback should create a new user in the database."""
    from pydatalab import config
    from pydatalab.routes.v0_1.auth import google_logged_in

    # Allow all Google users to register (no domain restriction)
    monkeypatch.setattr(config.CONFIG, "EMAIL_DOMAIN_ALLOW_LIST", None)

    # Simulate a successful response from the Google userinfo API
    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {
        "id": "google-id-999",
        "email": "tester@gmail.com",
        "name": "Google Tester",
    }

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        google_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    user = database.users.find_one({"identities.identifier": "google-id-999"})
    assert user is not None
    assert user["display_name"] == "Google Tester"


def test_google_login_no_token(database, app):
    """If no OAuth token is provided, no user should be created."""
    database.users.delete_many({})
    from pydatalab.routes.v0_1.auth import google_logged_in

    fake_blueprint = MagicMock()

    with app.test_request_context():
        result = google_logged_in(fake_blueprint, token=None)

    assert result is False
    assert database.users.find_one({"identities.identity_type": "google"}) is None


def test_google_login_bad_api_response(database, app):
    """If the Google API returns an error, no user should be created."""
    from pydatalab.routes.v0_1.auth import google_logged_in

    fake_resp = MagicMock()
    fake_resp.ok = False  # Google API failed

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        result = google_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    assert result is False
    assert database.users.find_one({"identities.identity_type": "google"}) is None


# ──────────────────────────────────────────────
# Microsoft OAuth tests
# ──────────────────────────────────────────────


def test_microsoft_login_success(database, app, monkeypatch):
    """A valid Microsoft OAuth callback should create a new user in the database."""
    from pydatalab import config
    from pydatalab.routes.v0_1.auth import microsoft_logged_in

    # Allow all Microsoft users to register (no domain restriction)
    monkeypatch.setattr(config.CONFIG, "EMAIL_DOMAIN_ALLOW_LIST", None)

    monkeypatch.setattr(config.CONFIG, "AUTO_ACTIVATE_ACCOUNTS", True)

    # Simulate a successful response from the Microsoft Graph API
    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {
        "id": "ms-id-001",
        "mail": "tester@outlook.com",
        "displayName": "MS Tester",
    }

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        microsoft_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    user = database.users.find_one({"identities.identifier": "ms-id-001"})
    assert user is not None
    assert user["display_name"] == "MS Tester"


def test_microsoft_login_no_token(database, app):
    """If no OAuth token is provided, no user should be created."""
    database.users.delete_many({})
    from pydatalab.routes.v0_1.auth import microsoft_logged_in

    fake_blueprint = MagicMock()

    with app.test_request_context():
        result = microsoft_logged_in(fake_blueprint, token=None)

    assert result is False
    assert database.users.find_one({"identities.identity_type": "microsoft"}) is None


def test_microsoft_login_bad_api_response(database, app):
    """If the Microsoft API returns an error, no user should be created."""
    from pydatalab.routes.v0_1.auth import microsoft_logged_in

    fake_resp = MagicMock()
    fake_resp.ok = False  # Microsoft API failed

    fake_blueprint = MagicMock()
    fake_blueprint.session.get.return_value = fake_resp

    with app.test_request_context():
        result = microsoft_logged_in(fake_blueprint, token={"access_token": "fake-token"})

    assert result is False
    assert database.users.find_one({"identities.identity_type": "microsoft"}) is None
