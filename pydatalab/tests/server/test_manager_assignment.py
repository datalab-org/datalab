from bson import ObjectId


def test_assign_manager_success(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = user_1.inserted_id

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = user_2.inserted_id

    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})

    response = admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})

    assert response.status_code == 200

    updated_user = db.users.find_one({"_id": user_2.inserted_id})
    assert user_1_id in updated_user["managers"]

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})
    db.roles.delete_one({"_id": user_1.inserted_id})


def test_assign_manager_requires_admin(client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = user_1.inserted_id

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = user_2.inserted_id

    response = client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})

    assert response.status_code == 403

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})


def test_assign_manager_prevents_direct_cycle(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = user_1.inserted_id

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = user_2.inserted_id

    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})
    db.roles.insert_one({"_id": user_2.inserted_id, "role": "manager"})

    response = admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    assert response.status_code == 200

    response = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_2_id]})

    assert response.status_code == 400
    assert "circular" in response.json["message"].lower()

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})
    db.roles.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})


def test_manager_double_cycle(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})

    user_1_id = user_1.inserted_id

    user_2 = db.users.insert_one({"display_name": "User 2"})
    db.roles.insert_one({"_id": user_2.inserted_id, "role": "manager"})
    user_2_id = user_2.inserted_id

    user_3 = db.users.insert_one({"display_name": "User 3"})
    db.roles.insert_one({"_id": user_3.inserted_id, "role": "manager"})
    user_3_id = user_3.inserted_id

    user_4 = db.users.insert_one({"display_name": "User 4"})
    db.roles.insert_one({"_id": user_4.inserted_id, "role": "manager"})
    user_4_id = user_4.inserted_id

    # Check that the following hierarchy is forbidden:
    # I. 1 managers 3
    # II. 2 and 3 manage 4
    # III. 4 managers 1
    # i.e., second manager of 4 blocks the final clause
    admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_4_id}/managers", json={"managers": [user_2_id, user_3_id]})
    resp = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_4_id]})
    assert resp.status_code != 200
    assert "circular" in resp.json["message"].lower()

    # In either direction
    admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_4_id}/managers", json={"managers": [user_3_id, user_2_id]})
    resp = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_4_id]})
    assert resp.status_code != 200
    assert "circular" in resp.json["message"].lower()

    # But instead,
    # IIIb. 2 manages 1
    # is allowed.
    resp = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_2_id]})
    assert resp.status_code == 200

    db.users.delete_many(
        {
            "_id": {
                "$in": [
                    user_1.inserted_id,
                    user_2.inserted_id,
                    user_3.inserted_id,
                    user_4.inserted_id,
                ]
            }
        }
    )
    db.roles.delete_many(
        {
            "_id": {
                "$in": [
                    user_1.inserted_id,
                    user_2.inserted_id,
                    user_3.inserted_id,
                    user_4.inserted_id,
                ]
            }
        }
    )


def test_manager_double_cycle_inverse(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    db.roles.insert_one({"_id": user_2.inserted_id, "role": "manager"})
    user_2_id = str(user_2.inserted_id)

    user_3 = db.users.insert_one({"display_name": "User 3"})
    db.roles.insert_one({"_id": user_3.inserted_id, "role": "manager"})
    user_3_id = str(user_3.inserted_id)

    user_4 = db.users.insert_one({"display_name": "User 4"})
    db.roles.insert_one({"_id": user_4.inserted_id, "role": "manager"})
    user_4_id = str(user_4.inserted_id)

    user_5 = db.users.insert_one({"display_name": "User 5"})
    db.roles.insert_one({"_id": user_5.inserted_id, "role": "manager"})
    user_5_id = str(user_5.inserted_id)

    # Similar to the above, check that the following hierarchy is forbidden:
    # I. 1 manages 2 and 3
    # II. 3 manages 4
    # III. 4 and 5 manages 1 (and then 5 and 4)
    # i.e., second manager of 1 blocks the final clause
    admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_4_id}/managers", json={"managers": [user_3_id]})
    resp = admin_client.patch(
        f"/users/{user_1_id}/managers", json={"managers": [user_4_id, user_5_id]}
    )
    assert resp.status_code != 200
    assert "circular" in resp.json["message"].lower()

    # In either direction
    admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_4_id}/managers", json={"managers": [user_3_id]})
    resp = admin_client.patch(
        f"/users/{user_1_id}/managers", json={"managers": [user_5_id, user_4_id]}
    )
    assert resp.status_code != 200
    assert "circular" in resp.json["message"].lower()


def test_assign_manager_prevents_deep_cycle(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = str(user_2.inserted_id)

    user_3 = db.users.insert_one({"display_name": "User 3"})
    user_3_id = str(user_3.inserted_id)

    for uid in [user_1.inserted_id, user_2.inserted_id, user_3.inserted_id]:
        db.roles.insert_one({"_id": uid, "role": "manager"})

    admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_2_id]})

    response = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_3_id]})

    assert response.status_code == 400
    assert "circular" in response.json["message"].lower()

    db.users.delete_many(
        {"_id": {"$in": [user_1.inserted_id, user_2.inserted_id, user_3.inserted_id]}}
    )
    db.roles.delete_many(
        {"_id": {"$in": [user_1.inserted_id, user_2.inserted_id, user_3.inserted_id]}}
    )


def test_assign_manager_allows_hierarchy(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = str(user_2.inserted_id)

    user_3 = db.users.insert_one({"display_name": "User 3"})
    user_3_id = str(user_3.inserted_id)

    for uid in [user_1.inserted_id, user_2.inserted_id]:
        db.roles.insert_one({"_id": uid, "role": "manager"})

    response = admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    assert response.status_code == 200

    response = admin_client.patch(f"/users/{user_3_id}/managers", json={"managers": [user_2_id]})
    assert response.status_code == 200

    db.users.delete_many(
        {"_id": {"$in": [user_1.inserted_id, user_2.inserted_id, user_3.inserted_id]}}
    )
    db.roles.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})


def test_remove_manager_assignment(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2", "managers": [user_1_id]})
    user_2_id = str(user_2.inserted_id)

    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})

    response = admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": []})

    assert response.status_code == 200

    updated_user = db.users.find_one({"_id": user_2.inserted_id})
    assert updated_user["managers"] == []

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})
    db.roles.delete_one({"_id": user_1.inserted_id})


def test_assign_nonexistent_manager(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    fake_id = str(ObjectId())

    response = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [fake_id]})

    assert response.status_code == 404

    db.users.delete_one({"_id": user_1.inserted_id})


def test_assign_manager_invalid_format(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    response = admin_client.patch(
        f"/users/{user_1_id}/managers", json={"managers": ["not-a-valid-id"]}
    )

    assert response.status_code == 400

    db.users.delete_one({"_id": user_1.inserted_id})


def test_manager_can_see_managed_user_items(admin_client, real_mongo_client, user_id):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})

    response = admin_client.patch(f"/users/{str(user_id)}/managers", json={"managers": [user_1_id]})
    assert response.status_code == 200

    response = admin_client.post(
        "/new-sample/", json={"item_id": "test-managed-sample", "type": "samples"}
    )
    assert response.status_code == 201

    response = admin_client.get("/get-item-data/test-managed-sample")
    assert response.status_code == 200
    refcode = response.json["item_data"]["refcode"]

    response = admin_client.patch(
        f"/items/{refcode}/permissions", json={"creators": [{"immutable_id": str(user_id)}]}
    )
    assert response.status_code == 200

    db.users.delete_one({"_id": user_1.inserted_id})
    db.roles.delete_one({"_id": user_1.inserted_id})


def test_manager_cycle_infinite_loop(admin_client, real_mongo_client):
    """Tests that a long linear chain of managers is impossible to create via the API after depth ~10."""
    db = real_mongo_client.get_database()

    user_docs = [{"display_name": f"User {i}"} for i in range(1, 100)]
    ids = db.users.insert_many(user_docs)
    for inserted_id in ids.inserted_ids:
        db.roles.insert_one({"_id": inserted_id, "role": "manager"})
    for i in range(len(ids.inserted_ids) - 1):
        resp = admin_client.patch(
            f"/users/{str(ids.inserted_ids[i + 1])}/managers",
            json={"managers": [str(ids.inserted_ids[i])]},
        )

        # Queryer will reject after depth 10 by default, in our case that corresponds to user 9 managing user 10
        if i < 9:
            assert resp.status_code == 200
        else:
            assert resp.status_code == 500
            assert "maximum management hierarchy depth exceeded" in resp.json["message"].lower()
            break
    else:
        assert False, "Expected to break from loop due to cycle detection"
