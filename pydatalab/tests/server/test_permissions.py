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

    # Admin needs ?sudo=1 to see another user's item
    response = admin_client.get(f"/items/{refcode}")
    assert response.status_code == 404

    response = admin_client.get(f"/items/{refcode}?sudo=1")
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


def test_manager_permissions(
    admin_client, client, another_client, user_id, another_user_id, real_mongo_client
):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "private-sample-with-manager"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    # Add manager to the original user
    response = admin_client.patch(
        f"/users/{user_id}/managers", json={"managers": [str(another_user_id)]}
    )
    assert response.status_code == 200

    # Manager gets read access
    assert client.get(f"/items/{refcode}").status_code == 200

    # Manager gets read access
    assert another_client.get(f"/items/{refcode}").status_code == 200

    # Manager also gets write access
    assert (
        another_client.post(
            "/save-item/",
            json={"item_id": "private-sample-with-manager", "data": {"description": "set"}},
        ).status_code
        == 200
    )

    # Remove manager from the original user
    response = admin_client.patch(f"/users/{user_id}/managers", json={"managers": []})
    assert response.status_code == 200

    # Also removes read access
    assert another_client.get(f"/items/{refcode}").status_code == 404


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


def test_append_permissions_creators(client, another_client, user_id, another_user_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-append-test"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    original_creators = response.json["item_data"]["creators"]
    assert len(original_creators) == 1

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    updated_creators = response.json["item_data"]["creators"]
    assert len(updated_creators) == 2

    creator_ids = response.json["item_data"]["creator_ids"]
    assert str(user_id) in creator_ids
    assert str(another_user_id) in creator_ids


def test_append_permissions_groups(client, another_client, user_id, another_user_id, group_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-group-append-test"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    original_groups = response.json["item_data"].get("groups", [])
    assert len(original_groups) == 0

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"groups": [{"immutable_id": str(group_id)}]},
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    updated_groups = response.json["item_data"]["groups"]
    assert len(updated_groups) == 1

    group_ids = response.json["item_data"]["group_ids"]
    assert str(group_id) in group_ids


def test_append_permissions_no_duplicates(client, another_user_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-duplicate-test"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200
    assert response.json["message"] == "No changes needed"

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    creators = response.json["item_data"]["creators"]
    assert len(creators) == 2


def test_append_permissions_both_creators_and_groups(client, another_user_id, group_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-both-append-test"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.put(
        f"/items/{refcode}/permissions",
        json={
            "creators": [{"immutable_id": str(another_user_id)}],
            "groups": [{"immutable_id": str(group_id)}],
        },
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    item_data = response.json["item_data"]
    assert len(item_data["creators"]) == 2
    assert len(item_data["groups"]) == 1


def test_append_permissions_invalid_user(client):
    from bson import ObjectId

    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-invalid-user"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    fake_user_id = str(ObjectId())
    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": fake_user_id}]},
    )
    assert response.status_code == 400
    assert "not found in the database" in response.json["message"]


def test_patch_vs_put_permissions(client, user_id, another_user_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-patch-vs-put"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    creators_after_put = response.json["item_data"]["creators"]
    assert len(creators_after_put) == 2

    creator_ids_after_put = response.json["item_data"]["creator_ids"]
    assert str(user_id) in creator_ids_after_put
    assert str(another_user_id) in creator_ids_after_put

    response = client.patch(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(user_id)}]},
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    creators_after_patch = response.json["item_data"]["creators"]
    assert len(creators_after_patch) == 1

    creator_ids_after_patch = response.json["item_data"]["creator_ids"]
    assert str(user_id) in creator_ids_after_patch
    assert str(another_user_id) not in creator_ids_after_patch


def test_append_permissions_preserves_base_owner(client, another_user_id):
    response = client.post(
        "/new-sample/", json={"type": "samples", "item_id": "sample-for-owner-preservation"}
    )
    assert response.status_code == 201
    refcode = response.json["sample_list_entry"]["refcode"]

    response = client.get(f"/items/{refcode}")
    original_owner_id = response.json["item_data"]["creator_ids"][0]

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    creator_ids_after_first_append = response.json["item_data"]["creator_ids"]
    assert len(creator_ids_after_first_append) == 2
    assert creator_ids_after_first_append[0] == original_owner_id

    response = client.put(
        f"/items/{refcode}/permissions",
        json={"creators": [{"immutable_id": str(another_user_id)}]},
    )
    assert response.status_code == 200
    assert response.json["message"] == "No changes needed"

    response = client.get(f"/items/{refcode}")
    assert response.status_code == 200
    creator_ids_final = response.json["item_data"]["creator_ids"]
    assert len(creator_ids_final) == 2
    assert creator_ids_final[0] == original_owner_id


def test_admin_super_user_mode(admin_client, client):
    """Test that admins must opt-in to super-user mode with ?sudo=1 for GET requests.

    - Admin GET without ?sudo=1: should only see own items (not other users' items)
    - Admin GET with ?sudo=1: should see all items
    - Non-admin GET with ?sudo=1: should only see own items (param ignored)
    - Admin non-GET methods: should always have full access (no ?sudo=1 needed)
    """
    # Create a sample as a normal user
    response = client.post("/new-sample/", json={"type": "samples", "item_id": "user-owned-sample"})
    assert response.status_code == 201
    user_refcode = response.json["sample_list_entry"]["refcode"]

    # Create a sample as an admin
    response = admin_client.post(
        "/new-sample/", json={"type": "samples", "item_id": "admin-owned-sample"}
    )
    assert response.status_code == 201
    admin_refcode = response.json["sample_list_entry"]["refcode"]

    # Admin without ?sudo=1 cannot see user's item on GET
    response = admin_client.get(f"/items/{user_refcode}")
    assert response.status_code == 404

    # Admin with ?sudo=1 can see user's item on GET
    response = admin_client.get(f"/items/{user_refcode}?sudo=1")
    assert response.status_code == 200

    # Admin can always see their own item (no ?sudo=1 needed)
    response = admin_client.get(f"/items/{admin_refcode}")
    assert response.status_code == 200

    # Normal user with ?sudo=1 still cannot see admin's item (param ignored for non-admins)
    response = client.get(f"/items/{admin_refcode}?sudo=1")
    assert response.status_code == 404

    # Normal user can see their own item
    response = client.get(f"/items/{user_refcode}")
    assert response.status_code == 200

    # Admin can still PATCH/DELETE user's item without ?sudo=1 (non-GET methods unaffected)
    response = admin_client.patch(f"/items/{user_refcode}/permissions", json={"creators": []})
    assert response.status_code == 200


def test_collection_permissions_update(admin_client, client, user_id, another_client):
    """Admin creates a collection, shares it with a normal user via the
    `/collections/<id>/permissions` endpoint, and verifies that the user can
    then access it (whilst a third user still cannot)."""

    collection_id = "shared-collection"
    response = admin_client.put(
        "/collections",
        json={
            "data": {
                "collection_id": collection_id,
                "title": "Shared collection",
                "type": "collections",
            }
        },
    )
    assert response.status_code == 201, response.json

    # Normal user cannot see it yet
    assert client.get(f"/collections/{collection_id}").status_code == 404
    # And it does not show up in their listing
    listing = client.get("/collections").json["data"]
    assert all(c["collection_id"] != collection_id for c in listing)

    # Admin shares the collection with the normal user
    response = admin_client.patch(
        f"/collections/{collection_id}/permissions",
        json={"creators": [{"immutable_id": str(user_id)}]},
    )
    assert response.status_code == 200, response.json

    # Normal user can now access it
    response = client.get(f"/collections/{collection_id}")
    assert response.status_code == 200, response.json
    assert response.json["data"]["collection_id"] == collection_id

    # And it now appears in their listing
    listing = client.get("/collections").json["data"]
    assert any(c["collection_id"] == collection_id for c in listing)

    # A third user without permission still cannot see it, nor does it show
    # up in their listing
    assert another_client.get(f"/collections/{collection_id}").status_code == 404
    listing = another_client.get("/collections").json["data"]
    assert all(c["collection_id"] != collection_id for c in listing)

    # A non-permitted user cannot grant themselves access
    response = another_client.patch(
        f"/collections/{collection_id}/permissions",
        json={"creators": [{"immutable_id": str(user_id)}]},
    )
    assert response.status_code != 200


def test_collection_create_with_inlined_groups(admin_client, database, group_id):
    """Creating a collection with an inlined `groups` payload (as the frontend
    sends) should populate `group_ids` in the stored document, but should NOT
    persist the inlined `groups` field — that is reserved for the read-time
    `$lookup` join."""

    collection_id = "collection-with-inlined-groups"
    response = admin_client.put(
        "/collections",
        json={
            "data": {
                "collection_id": collection_id,
                "title": "Collection with inlined groups",
                "type": "collections",
                "groups": [{"immutable_id": str(group_id)}],
            }
        },
    )
    assert response.status_code == 201, response.json

    stored = database.collections.find_one({"collection_id": collection_id})
    assert stored is not None
    assert stored.get("group_ids") == [group_id]
    # The inlined `groups` payload from the request must not be persisted —
    # otherwise the read-time $lookup is shadowed by stale data.
    assert "groups" not in stored or stored["groups"] is None


def test_collection_visible_via_group_membership(admin_client, client, another_client, group_id):
    """A collection shared with a group should be visible (both via the
    listing and the detail endpoint) to all members of that group, not just
    direct creators."""

    collection_id = "group-shared-collection"
    response = admin_client.put(
        "/collections",
        json={
            "data": {
                "collection_id": collection_id,
                "title": "Group-shared collection",
                "type": "collections",
                "groups": [{"immutable_id": str(group_id)}],
            }
        },
    )
    assert response.status_code == 201, response.json

    # Both group members can see it on the detail endpoint
    assert client.get(f"/collections/{collection_id}").status_code == 200
    assert another_client.get(f"/collections/{collection_id}").status_code == 200

    # And, crucially, it must show up on the listing endpoint — the listing
    # match must not be constrained to user_only permissions, otherwise
    # group-shared collections never appear.
    for c in (client, another_client):
        listing = c.get("/collections").json["data"]
        assert any(entry["collection_id"] == collection_id for entry in listing), (
            f"group-shared collection missing from /collections listing for {c}"
        )


def test_collection_permissions_update_via_group(admin_client, client, another_client, group_id):
    """Admin creates a collection, then shares it with a group via the
    `/collections/<id>/permissions` endpoint, and verifies that members of
    that group can access it (both detail and listing)."""

    collection_id = "group-shared-via-patch"
    response = admin_client.put(
        "/collections",
        json={
            "data": {
                "collection_id": collection_id,
                "title": "Group-shared via PATCH",
                "type": "collections",
            }
        },
    )
    assert response.status_code == 201, response.json

    # Group members cannot see it yet
    assert client.get(f"/collections/{collection_id}").status_code == 404
    listing = client.get("/collections").json["data"]
    assert all(c["collection_id"] != collection_id for c in listing)

    # Admin shares the collection with the group
    response = admin_client.patch(
        f"/collections/{collection_id}/permissions",
        json={"groups": [{"immutable_id": str(group_id)}]},
    )
    assert response.status_code == 200, response.json

    # Both group members now have access via detail and listing
    for c in (client, another_client):
        response = c.get(f"/collections/{collection_id}")
        assert response.status_code == 200, response.json
        assert response.json["data"]["collection_id"] == collection_id

        listing = c.get("/collections").json["data"]
        assert any(entry["collection_id"] == collection_id for entry in listing)
