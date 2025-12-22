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


def test_basic_permissions_update(admin_client, admin_user_id, client, user_id, another_client):
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
    response = admin_client.patch(
        f"/items/{refcode}/permissions", json={"creators": [{"immutable_id": str(admin_user_id)}]}
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 404

    # but that the admin still remains the creator
    response = admin_client.get(f"/items/{refcode}")
    assert response.status_code == 200


def test_access_token_permissions(client, unauthenticated_client, admin_client, database):
    response = client.post("/new-sample/", json={"type": "samples", "item_id": "private-sample"})
    assert response.status_code == 201
    response = response.json

    refcode = response["sample_list_entry"]["refcode"]
    assert refcode

    response = client.post(f"/items/{refcode}/issue-access-token")
    response = response.json
    assert response["status"] == "success"
    token = response["token"]
    assert token

    response = unauthenticated_client.get(f"/items/{refcode}")
    assert response.status_code == 401

    response = unauthenticated_client.get(f"/items/{refcode}?at={token}")
    assert response.status_code == 200

    response = unauthenticated_client.get(f"/items/{refcode}?at={token}123")
    assert response.status_code == 401

    response = admin_client.get(f"/items/{refcode}")
    assert response.status_code == 200

    response = admin_client.get(f"/items/{refcode}?at={token}")
    assert response.status_code == 200

    database.api_keys.delete_many({"type": "access_token"})

    response = admin_client.get(f"/items/{refcode}?at={token}")
    assert response.status_code == 401

    response = client.get(f"/items/{refcode}?at={token}")
    assert response.status_code == 401

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200

    response = unauthenticated_client.get(f"/items/{refcode}?at={token}")
    assert response.status_code == 401


def test_group_permissions(client, another_client, user_id, another_user_id, group_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "private-sample-in-a-group"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.patch(
        f"/items/{refcode}/permissions",
        json={"groups": [{"immutable_id": str(group_id)}]},
    )

    # Group membership gives read access
    assert another_client.get(f"/items/{refcode}").status_code == 200

    # But not write access, which returns 404 Not Found as the user cannot "see" the item
    assert (
        another_client.post(
            "/save-item/", json={"item_id": "private-sample-in-a-group", "data": {"group_ids": []}}
        ).status_code
        == 404
    )
    # Removing the group removes access
    response = client.patch(
        f"/items/{refcode}/permissions",
        json={"groups": []},
    )

    assert response.status_code == 200

    # Also removes read access
    assert another_client.get(f"/items/{refcode}").status_code == 404
