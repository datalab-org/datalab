from bson import ObjectId


def test_assign_manager_success(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = str(user_2.inserted_id)

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
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = str(user_2.inserted_id)

    response = client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})

    assert response.status_code == 403

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})


def test_assign_manager_prevents_direct_cycle(admin_client, real_mongo_client):
    db = real_mongo_client.get_database()

    user_1 = db.users.insert_one({"display_name": "User 1"})
    user_1_id = str(user_1.inserted_id)

    user_2 = db.users.insert_one({"display_name": "User 2"})
    user_2_id = str(user_2.inserted_id)

    db.roles.insert_one({"_id": user_1.inserted_id, "role": "manager"})
    db.roles.insert_one({"_id": user_2.inserted_id, "role": "manager"})

    response = admin_client.patch(f"/users/{user_2_id}/managers", json={"managers": [user_1_id]})
    assert response.status_code == 200

    response = admin_client.patch(f"/users/{user_1_id}/managers", json={"managers": [user_2_id]})

    assert response.status_code == 400
    assert "circular" in response.json["message"].lower()

    db.users.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})
    db.roles.delete_many({"_id": {"$in": [user_1.inserted_id, user_2.inserted_id]}})


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
