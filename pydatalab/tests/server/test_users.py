def test_get_current_user_unauthenticated(unauthenticated_client):
    """Test that the API key for the demo user has been set correctly."""

    resp = unauthenticated_client.get("/get-current-user/")
    assert resp.status_code == 401


def test_get_current_user(client, database):
    """Test that the API key for the demo user has been set correctly."""

    resp = client.get("/get-current-user/")
    assert resp.status_code == 200
    assert (resp_json := resp.json)
    assert resp_json["immutable_id"] == 24 * "1"
    assert resp_json["role"] == "user"
    assert resp_json["groups"][0]["immutable_id"] == 24 * "2"
    assert resp_json["groups"][0]["group_id"] == "demo"
    assert resp_json["groups"][0]["display_name"] == "Demo Group"


def test_get_current_user_admin(admin_client):
    """Test that the API key for the demo admin has been set correctly."""
    resp = admin_client.get("/get-current-user/")
    assert (resp_json := resp.json)
    assert resp_json["immutable_id"] == 24 * "8"
    assert resp_json["role"] == "admin"


def test_role(admin_client, database, user_id):
    endpoint = f"/roles/{str(user_id)}"
    admin_request = {"role": "manager"}
    resp = admin_client.patch(endpoint, json=admin_request)
    assert resp.status_code == 200
    user = database.roles.find_one({"_id": user_id})
    assert user["role"] == "manager"


def test_role_update_by_user(client, database, user_id):
    endpoint = f"/roles/{str(user_id)}"
    user_request = {"role": "admin"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 403
    user = database.roles.find_one({"_id": user_id})
    assert user["role"] == "manager"


def test_list_users(admin_client, client):
    resp = admin_client.get("/users")
    assert resp.status_code == 200
    resp = client.get("/users")
    assert resp.status_code == 403


def test_list_groups(admin_client, client):
    resp = admin_client.get("/groups")
    assert resp.status_code == 200
    resp = client.get("/groups")
    assert resp.status_code == 403


def test_user_update(client, unauthenticated_client, database, user_id, admin_user_id):
    endpoint = f"/users/{str(user_id)}"
    # Test display name update
    user_request = {"display_name": "Test Person II"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test contact email update
    user_request = {"contact_email": "test2@example.org"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["contact_email"] == "test2@example.org"
    assert user["identities"][-1]["identifier"] == "test2@example.org"
    assert not user["identities"][-1]["verified"]

    # Test that display name -> None does not remove display name
    user_request = {"display_name": None}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test that contact_email -> None or empty DOES remove email
    user_request = {"contact_email": None}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Check empty string does the same, but reset email first
    user_request = {"contact_email": "test2@example.org"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["contact_email"] == "test2@example.org"
    user_request = {"contact_email": ""}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Test bad display name does not update
    user_request = {"display_name": " "}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 400
    user = database.users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person II"

    # Test bad contact email does not update
    user_request = {"contact_email": "not_an_email"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 400
    user = database.users.find_one({"_id": user_id})
    assert user["contact_email"] is None

    # Test that user cannot update admin account
    endpoint = f"/users/{str(admin_user_id)}"
    user_request = {"display_name": "Test Person"}
    resp = client.patch(endpoint, json=user_request)
    assert resp.status_code == 403
    user = database.users.find_one({"_id": admin_user_id})
    assert user["display_name"] == "Test Admin"

    # Test that differing user auth can/cannot search for users
    endpoint = "/search-users/"
    resp = client.get(endpoint + "?query='Test Person'")
    assert resp.status_code == 200
    assert len(resp.json["users"]) == 2

    endpoint = "/search/users/"
    resp = client.get(endpoint + "?query='Test Person'")
    assert resp.status_code == 200
    assert len(resp.json["users"]) == 2

    # Test that differing user auth can/cannot search for users
    resp = unauthenticated_client.get(endpoint + "?query='Test Person'")
    assert resp.status_code == 401


def test_user_update_admin(admin_client, database, user_id):
    endpoint = f"/users/{str(user_id)}"
    # Test admin override of display name
    user_request = {"display_name": "Test Person"}
    resp = admin_client.patch(endpoint, json=user_request)
    assert resp.status_code == 200
    user = database.users.find_one({"_id": user_id})
    assert user["display_name"] == "Test Person"


def test_groups(
    admin_client, client, unauthenticated_client, database, admin_user_id, user_id, another_user_id
):
    from bson import ObjectId

    good_group = {
        "display_name": "My New Group",
        "group_id": "my-new-group",
        "description": "A group for testing",
        "managers": [],
    }

    # Group ID cannot be None
    bad_group = good_group.copy()
    bad_group["group_id"] = None
    resp = admin_client.put("/groups", json=bad_group)
    assert resp.status_code == 400

    # Successfully create group
    resp = admin_client.put("/groups", json=good_group)
    assert resp.status_code == 200
    group_immutable_id = ObjectId(resp.json["group_immutable_id"])
    assert database.groups.find_one({"_id": group_immutable_id})

    # Group ID must be unique
    resp = admin_client.put("/groups", json=good_group)
    assert resp.status_code == 400

    # Request must come from admin
    # Make ID unique so that this would otherwise pass
    good_group["group_id"] = "my-new-group-2"
    resp = unauthenticated_client.put("/groups", json=good_group)
    assert resp.status_code == 401
    assert database.groups.find_one({"group_id": good_group["group_id"]}) is None

    # Request must come from admin
    resp = client.put("/groups", json=good_group)
    assert resp.status_code == 403
    assert database.groups.find_one({"group_id": good_group["group_id"]}) is None

    # Check a user can search groups
    resp = client.get("/search/groups?query=New")
    assert resp.status_code == 200
    assert len(resp.json["data"]) == 1

    # Check that a user can be added to the group by an admin
    resp = admin_client.put(f"/groups/{group_immutable_id}", json={"user_id": another_user_id})
    assert resp.status_code == 200

    user_groups = database.users.find_one({"_id": ObjectId(another_user_id)})["groups"]
    assert user_groups[1]["immutable_id"] == group_immutable_id
    assert len(user_groups) == 2

    # Check that repeated addition is idempotent
    resp = admin_client.put(f"/groups/{group_immutable_id}", json={"user_id": another_user_id})
    assert resp.status_code == 304

    user_groups = database.users.find_one({"_id": ObjectId(another_user_id)})["groups"]
    assert len(user_groups) == 2

    # Test that an admin can update a group's details/managers
    new_details = {
        "display_name": "My Newly Named Group",
        "group_id": "my-new-group-renamed",
        "description": "A group for testing the group update mechanism",
        "managers": [admin_user_id, user_id, another_user_id],
    }

    resp = admin_client.patch(f"/groups/{group_immutable_id}", json=new_details)
    assert resp.status_code == 200
    assert database.groups.find_one({"group_id": new_details["group_id"]}) is not None

    # Now remove the user from the group and make sure they are also removed from the managers list
    resp = admin_client.delete(f"/groups/{group_immutable_id}/members/{another_user_id}")

    assert resp.status_code == 200
    user_groups = database.users.find_one({"_id": ObjectId(another_user_id)})["groups"]
    assert len(user_groups) == 1

    managers = database.groups.find_one({"_id": group_immutable_id})["managers"]
    assert ObjectId(another_user_id) not in managers
