def test_get_current_user_unauthenticated(unauthenticated_client):
    """Test that the API key for the demo user has been set correctly."""

    resp = unauthenticated_client.get("/get-current-user/")
    assert resp.status_code == 401


def test_get_current_user(client):
    """Test that the API key for the demo user has been set correctly."""

    resp = client.get("/get-current-user/")
    assert resp.status_code == 200
    assert (resp_json := resp.json)
    assert resp_json["immutable_id"] == 24 * "1"
    assert resp_json["role"] == "user"


def test_get_current_user_admin(admin_client):
    """Test that the API key for the demo admin has been set correctly."""
    resp = admin_client.get("/get-current-user/")
    assert (resp_json := resp.json)
    assert resp_json["immutable_id"] == 24 * "8"
    assert resp_json["role"] == "admin"


def test_role(admin_client, real_mongo_client, user_id):
    endpoint = f"/roles/{str(user_id)}"
    admin_request = {"role": "manager"}
    resp = admin_client.patch(endpoint, json=admin_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().roles.find_one({"_id": user_id})
    assert user["role"] == "manager"


def test_role_update_by_user(client, real_mongo_client, user_id):
    endpoint = f"/roles/{str(user_id)}"
    user_request = {"role": "admin"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 403
    user = real_mongo_client.get_database().roles.find_one({"_id": user_id})
    assert user["role"] == "manager"


def test_user_update(client, real_mongo_client, user_id, admin_user_id):
    endpoint = f"/users/{str(user_id)}"
    # Test display name update
    user_request = {"display_name": "Test Person II"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test contact email update
    user_request = {"contact_email": "test2@example.org"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["contact_email"] == "test2@example.org"

    # Test that display name -> None does not remove display name
    user_request = {"display_name": None}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test that contact_email -> None or empty DOES remove email
    user_request = {"contact_email": None}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Check empty string does the same, but reset email first
    user_request = {"contact_email": "test2@example.org"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["contact_email"] == "test2@example.org"
    user_request = {"contact_email": ""}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Test bad display name does not update
    user_request = {"display_name": " "}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 400
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test bad contact email does not update
    user_request = {"contact_email": "not_an_email"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 400
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Test that user cannot update admin account
    endpoint = f"/users/{str(admin_user_id)}"
    user_request = {"display_name": "Test Person"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 403
    user = real_mongo_client.get_database().users.find_one({"_id": admin_user_id})
    assert user["display_name"] == "Test Admin"


def test_user_update_admin(admin_client, real_mongo_client, user_id):
    endpoint = f"/users/{str(user_id)}"
    # Test admin override of display name
    user_request = {"display_name": "Test Person"}
    resp = admin_client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = real_mongo_client.get_database().users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person"
