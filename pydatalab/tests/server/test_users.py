from pydatalab.models.people import Person


def test_get_current_user(client, insert_demo_user):
    """Test that the API key for the demo user has been set correctly."""

    resp = client.get("/get-current-user/")
    assert resp.status_code == 200


def test_user_update(client, real_mongo_client):
    example_user = Person(display_name="Test Person", contact_email="test@example.org").dict(
        exclude_unset=True, exclude_none=True
    )
    user_id = real_mongo_client.get_database().users.insert_one(example_user).inserted_id

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
