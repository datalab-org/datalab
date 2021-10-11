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
    assert response.status_code == 200, response.json
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
    assert response.status_code == 400
    assert response.json["message"] == "item_id_validation_error"


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
    assert (
        response.json["message"] == "Unable to update item '12345' (type = samples) with new data."
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
