# This file was edited with the assistance of an AI model and requires human review from the contributor.
import secrets
from hashlib import sha512

from bson import ObjectId

from pydatalab.models.people import AccountStatus
from pydatalab.mongo import gravatar_hash_for


def _insert_user_with_personal_data(database, other_user_id, group_id):
    new_user_id = ObjectId()
    api_key = secrets.token_hex(12)
    database.api_keys.insert_one(
        {
            "_id": ObjectId(),
            "user": new_user_id,
            "name": "testing API key",
            "hash": sha512(api_key.encode("utf-8")).hexdigest(),
            "type": "api_key",
        }
    )
    database.roles.insert_one({"_id": new_user_id, "role": "user"})
    database.users.insert_one(
        {
            "_id": new_user_id,
            "display_name": "To Be Deleted",
            "account_status": AccountStatus.ACTIVE,
            "groups": [{"immutable_id": group_id}],
            "contact_email": "deleteme@example.org",
            "gravatar_hash": gravatar_hash_for("deleteme@example.org"),
            "identities": [
                {
                    "identity_type": "email",
                    "identifier": "deleteme@example.org",
                    "name": "deleteme",
                    "verified": True,
                },
                {
                    "identity_type": "github",
                    "identifier": "123456",
                    "name": "deleteme-gh",
                    "verified": True,
                },
            ],
        }
    )
    database.magic_links.insert_one({"jwt": "abc", "email": "deleteme@example.org"})
    database.users.update_one({"_id": other_user_id}, {"$push": {"managers": new_user_id}})
    database.groups.update_one({"_id": group_id}, {"$push": {"managers": new_user_id}})
    return new_user_id, api_key


def test_tombstone_user(app, admin_client, database, another_user_id, group_id):
    user_id, api_key = _insert_user_with_personal_data(database, another_user_id, group_id)
    item_id = database.items.insert_one(
        {"item_id": "deleted_user_sample", "type": "samples", "creator_ids": [user_id]}
    ).inserted_id

    # Check that the user can log in before deletion
    headers = {"DATALAB-API-KEY": api_key}
    assert app.test_client().get("/get-current-user/", headers=headers).status_code == 200

    # Expunging should be refused as the user created an item
    resp = admin_client.delete(f"/users/{user_id}?expunge=true")
    assert resp.status_code == 409
    assert database.users.find_one({"_id": user_id})["display_name"] == "To Be Deleted"

    resp = admin_client.delete(f"/users/{user_id}")
    assert resp.status_code == 200
    display_name = resp.json["display_name"]
    assert display_name.endswith("(deleted user)")

    user = database.users.find_one({"_id": user_id})
    assert user["account_status"] == AccountStatus.DELETED
    assert user["display_name"] == display_name
    assert "identities" not in user
    assert user["contact_email"] is None
    assert user["groups"] == []
    assert user["gravatar_hash"] == gravatar_hash_for(None, display_name)

    assert database.api_keys.count_documents({"user": user_id}) == 0
    assert database.magic_links.count_documents({"email": "deleteme@example.org"}) == 0
    assert user_id not in database.users.find_one({"_id": another_user_id}).get("managers", [])
    assert user_id not in database.groups.find_one({"_id": group_id}).get("managers", [])

    # The item remains attributed to the tombstoned user
    assert database.items.find_one({"_id": item_id})["creator_ids"] == [user_id]

    # The user can no longer authenticate
    assert app.test_client().get("/get-current-user/", headers=headers).status_code == 401

    # A second user can also be tombstoned without clashing on the unique identities index
    second_user_id, _ = _insert_user_with_personal_data(database, another_user_id, group_id)
    resp = admin_client.delete(f"/users/{second_user_id}")
    assert resp.status_code == 200
    assert (
        database.users.find_one({"_id": second_user_id})["account_status"] == AccountStatus.DELETED
    )

    # The deleted status cannot be reverted
    resp = admin_client.patch(f"/users/{user_id}", json={"account_status": "active"})
    assert resp.status_code == 400
    assert database.users.find_one({"_id": user_id})["account_status"] == AccountStatus.DELETED


def test_expunge_user(admin_client, database, another_user_id, group_id):
    user_id, _ = _insert_user_with_personal_data(database, another_user_id, group_id)

    resp = admin_client.delete(f"/users/{user_id}?expunge=true")
    assert resp.status_code == 200

    assert database.users.find_one({"_id": user_id}) is None
    assert database.roles.find_one({"_id": user_id}) is None
    assert database.api_keys.count_documents({"user": user_id}) == 0
    assert database.magic_links.count_documents({"email": "deleteme@example.org"}) == 0
    assert user_id not in database.users.find_one({"_id": another_user_id}).get("managers", [])
    assert user_id not in database.groups.find_one({"_id": group_id}).get("managers", [])


def test_delete_user_permissions(client, admin_client, database, user_id, admin_user_id):
    resp = client.delete(f"/users/{user_id}")
    assert resp.status_code in (401, 403)
    assert database.users.find_one({"_id": user_id})["account_status"] == AccountStatus.ACTIVE

    resp = admin_client.delete(f"/users/{admin_user_id}")
    assert resp.status_code == 400

    resp = admin_client.delete(f"/users/{ObjectId()}")
    assert resp.status_code == 404

    resp = admin_client.patch(f"/users/{user_id}", json={"account_status": "deleted"})
    assert resp.status_code == 400
    assert database.users.find_one({"_id": user_id})["account_status"] == AccountStatus.ACTIVE
