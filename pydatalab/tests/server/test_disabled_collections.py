import pytest
from bson import ObjectId


# Register this module-local fixture as "app" so the shared client fixtures use an app with
# collections disabled instead of the standard app from conftest.py.
@pytest.fixture(scope="module", name="app")
def app_without_collections(real_mongo_client, app_config):
    """Create this module's API with collections disabled at startup."""
    from pydatalab.config import CONFIG
    from pydatalab.feature_flags import FEATURE_FLAGS
    from pydatalab.main import create_app
    from pydatalab.mongo import flask_mongo

    database_name = real_mongo_client.get_default_database().name
    real_mongo_client.drop_database(database_name)

    previous_setting = CONFIG.DISABLE_COLLECTIONS
    previous_flag = FEATURE_FLAGS.collections_enabled
    flask_app = create_app({**app_config, "DISABLE_COLLECTIONS": True}, env_file=False)

    yield flask_app

    if flask_mongo.cx:
        flask_mongo.cx.close()
    real_mongo_client.drop_database(database_name)
    CONFIG.DISABLE_COLLECTIONS = previous_setting
    FEATURE_FLAGS.collections_enabled = previous_flag


@pytest.mark.parametrize("prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_collection_routes_are_not_registered(client, prefix):
    assert client.get(f"{prefix}/collections").status_code == 404


def test_info_reports_collections_as_disabled(client):
    response = client.get("/info")

    assert response.status_code == 200
    assert response.json["data"]["attributes"]["features"]["collections_enabled"] is False


def _insert_collection_membership(database, another_user_id, group_id):
    collection_immutable_id = ObjectId()
    database.collections.insert_one(
        {
            "_id": collection_immutable_id,
            "collection_id": "collection-shared-item",
            "title": "Collection shared item",
            "type": "collections",
            "creator_ids": [another_user_id],
            "group_ids": [group_id],
        }
    )
    database.items.insert_one(
        {
            "item_id": "collection-only-item",
            "refcode": "test:COLL01",
            "type": "samples",
            "creator_ids": [another_user_id],
            "display_order": [],
            "file_ObjectIds": [],
            "relationships": [
                {
                    "type": "collections",
                    "immutable_id": collection_immutable_id,
                    "relation": None,
                    "description": "Is a member of",
                }
            ],
        }
    )
    return collection_immutable_id


def test_collection_membership_does_not_grant_item_access(
    client, another_client, database, another_user_id, group_id
):
    _insert_collection_membership(database, another_user_id, group_id)

    assert client.get("/items/test:COLL01").status_code == 404

    response = another_client.get("/items/test:COLL01")
    assert response.status_code == 200
    assert "collections" not in response.json["item_data"]
    assert all(
        relationship["type"] != "collections"
        for relationship in response.json["item_data"].get("relationships", [])
    )


def test_item_writes_ignore_collection_membership(client, database):
    collection_immutable_id = database.collections.insert_one(
        {
            "collection_id": "ignored-collection",
            "title": "Ignored collection",
            "type": "collections",
        }
    ).inserted_id

    response = client.post(
        "/new-sample/",
        json={
            "type": "samples",
            "item_id": "item-with-ignored-collection",
            "collections": [{"immutable_id": str(collection_immutable_id)}],
        },
    )

    assert response.status_code == 201
    assert "collections" not in response.json["sample_list_entry"]
    stored_item = database.items.find_one({"item_id": "item-with-ignored-collection"})
    assert all(
        relationship.get("type") != "collections"
        for relationship in stored_item.get("relationships", [])
    )


def test_collection_graphs_and_exports_are_unavailable(client):
    assert client.get("/item-graph?collection_id=ignored-collection").status_code == 404
    assert client.post("/collections/ignored-collection/export").status_code == 404
