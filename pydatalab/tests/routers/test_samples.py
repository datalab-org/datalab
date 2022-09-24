import datetime

import pytest


@pytest.mark.dependency()
def test_empty_samples(client):
    response = client.get("/samples/")
    assert len(response.json["samples"]) == 0
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_empty_samples"])
def test_new_sample(client, default_sample_dict):
    response = client.post("/new-sample/", json=default_sample_dict)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    for key in default_sample_dict.keys():
        if isinstance(v := default_sample_dict[key], datetime.datetime):
            v = v.isoformat()
        assert response.json["sample_list_entry"][key] == v


@pytest.mark.dependency(depends=["test_new_sample"])
def test_get_item_data(client, default_sample_dict):
    response = client.get("/get-item-data/12345")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_sample_dict.keys():
        if isinstance(v := default_sample_dict[key], datetime.datetime):
            v = v.isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_sample"])
def test_new_sample_collision(client, default_sample_dict):
    # Try to do the same thing again, expecting an ID collision
    response = client.post("/new-sample/", json=default_sample_dict)
    # Test that 409: Conflict is returned
    assert response.status_code == 409
    assert (
        response.json["message"] == "item_id_validation_error: '12345' already exists in database."
    )


@pytest.mark.dependency(depends=["test_new_sample"])
def test_save_good_sample(client, default_sample_dict):
    updated_sample = default_sample_dict.copy()
    updated_sample.update({"description": "This is a newer test sample."})
    response = client.post(
        "/save-item/",
        json={"item_id": default_sample_dict["item_id"], "data": updated_sample},
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    response = client.get("/get-item-data/12345")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_sample_dict.keys():
        if key in updated_sample and key in response.json:
            assert response.json[key] == updated_sample[key]


@pytest.mark.dependency(depends=["test_new_sample"])
def test_save_bad_sample(client, default_sample_dict):
    updated_sample = default_sample_dict.copy()
    updated_sample.update({"unknown_key": "This should not be allowed in."})
    response = client.post(
        "/save-item/",
        json={"item_id": default_sample_dict["item_id"], "data": updated_sample},
    )
    assert response.status_code == 400
    assert response.json["status"] == "error"
    assert response.json["message"].startswith(
        "Unable to update item item_id='12345' (item_type='samples') with new data"
    )


@pytest.mark.dependency(depends=["test_new_sample"])
def test_delete_sample(client, default_sample_dict):
    response = client.post(
        "/delete-sample/",
        json={"item_id": default_sample_dict["item_id"]},
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # Check it was actually deleted
    response = client.get(
        f"/get-item-data/{default_sample_dict['item_id']}",
    )
    assert response.status_code == 404


@pytest.mark.dependency(depends=["test_delete_sample"])
def test_create_indices(real_mongo_client):
    from pydatalab.mongo import create_default_indices

    if real_mongo_client is None:
        pytest.skip("Skipping FTS tests, not connected to real MongoDB")

    create_default_indices(real_mongo_client)
    indexes = list(real_mongo_client.get_database().items.list_indexes())
    expected_index_names = ("_id_", "item full-text search", "item type", "unique item ID")
    names = [index["name"] for index in indexes]

    assert all(name in names for name in expected_index_names)


@pytest.mark.dependency(depends=["test_create_indices"])
def test_full_text_search(client, real_mongo_client, example_items):

    if real_mongo_client is None:
        pytest.skip("Skipping FTS tests, not connected to real MongoDB")

    real_mongo_client.get_database().items.insert_many(example_items)

    response = client.get("/search-items/?query=12345&types=samples")

    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["item_id"] == "12345"

    response = client.get("/search-items/?query=new material")

    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert len(response.json["items"]) == 2
    assert response.json["items"][1]["item_id"] == "12345"
    assert response.json["items"][0]["item_id"] == "material"
