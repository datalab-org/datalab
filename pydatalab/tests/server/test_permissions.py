"""A set of non-exhaustive tests for user permissions in different scenarios."""


def test_unverified_user_permissions(unverified_client):
    """Test permissions for an unverified user."""
    client = unverified_client
    response = client.get("/samples/")
    assert response.status_code == 200

    response = client.post("/new-sample/", json={"type": "samples", "item_id": "test"})
    assert response.status_code == 401

    response = client.get("/starting-materials/")
    assert response.status_code == 200


def test_deactivated_user_permissions(deactivated_client):
    """Test permissions for a deactivated user."""
    client = deactivated_client
    response = client.get("/samples/")
    assert response.status_code == 200

    response = client.post("/new-sample/", json={"type": "samples", "item_id": "test"})
    assert response.status_code == 401

    response = client.get("/starting-materials/")
    assert response.status_code == 200


def test_unauthenticated_user_permissions(unauthenticated_client):
    """Test permissions for an unauthenticated user."""
    client = unauthenticated_client
    response = client.get("/samples/")
    assert response.status_code == 401

    response = client.post("/new-sample/", json={"type": "samples", "item_id": "test"})
    assert response.status_code == 401

    response = client.get("/starting-materials/")
    assert response.status_code == 401


def test_basic_permissions_update(admin_client, admin_user_id, client, user_id):
    """Test that an admin can share an item with a normal user."""

    response = admin_client.post(
        "/new-sample/", json={"type": "samples", "item_id": "test-admin-sample"}
    )
    assert response.status_code == 201

    response = admin_client.get("/get-item-data/test-admin-sample")
    assert response.status_code == 200
    refcode = response.json["item_data"]["refcode"]

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 404

    # Add normal user to the item
    response = admin_client.patch(
        f"/items/{refcode}/permissions", json={"creators": [{"immutable_id": str(user_id)}]}
    )
    assert response.status_code == 200

    # Check that they can now see it
    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200

    # Check that they cannot remove themselves/the admin from the creators
    client.patch(f"/items/{refcode}/permissions", json={"creators": []})
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200

    # Check that the admin can remove the user from the permissions
    response = admin_client.patch(f"/items/{refcode}/permissions", json={"creators": []})
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 404

    # but that the admin still remains the creator
    response = admin_client.get(f"/items/{refcode}")
    assert response.status_code == 200
