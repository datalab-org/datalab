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
