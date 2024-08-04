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
        if key == "creator_ids":
            continue
        if key in default_starting_material_dict:
            if isinstance(v := default_starting_material_dict[key], datetime.datetime):
                v = v.isoformat()
            assert value == v


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_get_item_data(admin_client, default_starting_material_dict):
    response = admin_client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # all starting materials should have no creators currently (they are shared among a deployment):
    assert len(response.json["item_data"]["creators"]) == 0
    assert len(response.json["item_data"]["creator_ids"]) == 0
    for key in default_starting_material_dict.keys():
        if key == "creator_ids":
            continue

        if isinstance(v := default_starting_material_dict[key], datetime.datetime):
            v = v.isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_starting_material", "test_get_item_data"])
def test_new_starting_material_with_automatically_generated_id(client):
    new_starting_material_data = {
        "name": "starting material with random id",
        "date": datetime.datetime.fromisoformat("1995-03-02"),
        "date_opened": datetime.datetime.fromisoformat("2001-12-31"),
        "chemform": "NiO",
        "type": "starting_materials",
        "CAS": "1313-99-1",
    }

    request_json = dict(
        new_sample_data=new_starting_material_data,
        generate_id_automatically=True,
    )

    response = client.post("/new-sample/", json=request_json)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    created_item_id = response.json["item_id"]
    assert created_item_id

    response = client.get(f"/get-item-data/{created_item_id}")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["item_data"]["refcode"].split(":")[1] == created_item_id

    for key in new_starting_material_data.keys():
        if key == "creator_ids":
            continue
        if isinstance(v := new_starting_material_data[key], datetime.datetime):
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
def test_save_good_starting_material(admin_client, default_starting_material_dict):
    updated_starting_material = default_starting_material_dict.copy()
    updated_starting_material.update({"description": "This is a newer test sample."})
    response = admin_client.post(
        "/save-item/",
        json={
            "item_id": default_starting_material_dict["item_id"],
            "data": updated_starting_material,
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    response = admin_client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_starting_material_dict.keys():
        if key in updated_starting_material and key in response.json:
            assert response.json[key] == updated_starting_material[key]


@pytest.mark.dependency(depends=["test_save_good_starting_material"])
def test_delete_starting_mateiral(admin_client, default_starting_material_dict):
    response = admin_client.post(
        "/delete-sample/",
        json={"item_id": default_starting_material_dict["item_id"]},
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # Check it was actually deleted
    response = admin_client.get(
        f"/get-item-data/{default_starting_material_dict['item_id']}",
    )
    assert response.status_code == 200
    assert "has been deleted" in response.json["warnings"][0]
