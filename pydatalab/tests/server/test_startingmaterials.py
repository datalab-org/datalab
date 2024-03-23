import datetime

import pytest


@pytest.mark.dependency()
def test_empty_starting_materials(client):
    response = client.get("/starting-materials/")
    assert len(response.json["items"]) == 0
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_empty_starting_materials"])
def test_new_starting_material(client, default_starting_material_dict):
    print(default_starting_material_dict)
    response = client.post("/new-sample/", json=default_starting_material_dict)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    print(response.json["sample_list_entry"])

    # all starting materials should have no creators currently (they are shared among a deployment):
    assert len(response.json["sample_list_entry"]["creators"]) == 0

    for key, value in response.json["sample_list_entry"].items():
        if key in default_starting_material_dict:
            if isinstance(v := default_starting_material_dict[key], datetime.datetime):
                v = v.isoformat()
            assert value == v


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_get_item_data(client, default_starting_material_dict):
    response = client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # all starting materials should have no creators currently (they are shared among a deployment):
    assert len(response.json["item_data"]["creators"]) == 0
    assert len(response.json["item_data"]["creator_ids"]) == 0

    for key in default_starting_material_dict.keys():
        if isinstance(v := default_starting_material_dict[key], datetime.datetime):
            v = v.isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_new_starting_material_collision(client, default_starting_material_dict):
    # Try to do the same thing again, expecting an ID collision
    response = client.post("/new-sample/", json=default_starting_material_dict)
    # Test that 409: Conflict is returned
    assert response.status_code == 409
    assert (
        response.json["message"]
        == "item_id_validation_error: 'test_sm' already exists in database."
    )


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_save_good_sample(client, default_starting_material_dict):
    updated_starting_material = default_starting_material_dict.copy()
    updated_starting_material.update({"description": "This is a newer test sample."})
    response = client.post(
        "/save-item/",
        json={
            "item_id": default_starting_material_dict["item_id"],
            "data": updated_starting_material,
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    response = client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_starting_material_dict.keys():
        if key in updated_starting_material and key in response.json:
            assert response.json[key] == updated_starting_material[key]


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_delete_sample(client, default_starting_material_dict):
    response = client.post(
        "/delete-sample/",
        json={"item_id": default_starting_material_dict["item_id"]},
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # Check it was actually deleted
    response = client.get(
        f"/get-item-data/{default_starting_material_dict['item_id']}",
    )
    assert response.status_code == 404
