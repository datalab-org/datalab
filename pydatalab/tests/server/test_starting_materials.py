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
                v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
            assert value == v


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_get_item_data(admin_client, default_starting_material_dict):
    response = admin_client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # all starting materials should have no creators currently (they are shared among a deployment):
    assert len(response.json["item_data"]["creators"]) == 0
    assert len(response.json["item_data"]["creator_ids"]) == 0
    for key in default_starting_material_dict:
        if key == "creator_ids":
            continue

        if isinstance(v := default_starting_material_dict[key], datetime.datetime):
            v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
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

    for key in new_starting_material_data:
        if key == "creator_ids":
            continue
        if isinstance(v := new_starting_material_data[key], datetime.datetime):
            v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_new_starting_material_collision(client, default_starting_material_dict):
    # Try to do the same thing again, expecting an ID collision
    response = client.post("/new-sample/", json=default_starting_material_dict)
    # Test that 409: Conflict is returned
    assert response.status_code == 409


@pytest.mark.dependency(depends=["test_new_starting_material"])
def test_save_good_starting_material(client, default_starting_material_dict):
    # Also test a change to the description and weird chemical formula
    updated_starting_material = {"description": "This is a newer test sample.", "chemform": "Xe/Ar"}
    response = client.post(
        "/save-item/",
        json={
            "item_id": default_starting_material_dict["item_id"],
            "data": updated_starting_material,
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    # Test a bad request
    response = client.post(
        "/save-item/",
        json={
            "item_ids": default_starting_material_dict["item_id"],
            "data": updated_starting_material,
        },
    )
    assert response.status_code == 400
    assert response.json["status"] == "error"
    assert "'item_id' to be passed in JSON request body" in response.json["message"]

    response = client.get("/get-item-data/test_sm")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_starting_material_dict:
        if key in updated_starting_material and key in response.json:
            assert response.json[key] == updated_starting_material[key]


@pytest.mark.dependency(depends=["test_save_good_starting_material"])
def test_delete_starting_material(admin_client, default_starting_material_dict):
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
    assert response.status_code == 404


@pytest.mark.dependency(depends=["test_delete_starting_material"])
def test_starting_material_permissions(
    admin_client, client, default_starting_material_dict, default_filepath
):
    response = admin_client.post("/new-sample/", json=default_starting_material_dict)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    # Check that an admin-created inventory item can be edited by a normal user, and have files attached to it
    response = client.get(
        f"/get-item-data/{default_starting_material_dict['item_id']}",
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    with open(default_filepath, "rb") as f:
        response = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": default_starting_material_dict["item_id"],
                "file": [(f, default_filepath.name)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )

    assert isinstance(response.json["file_id"], str)
    assert response.json["file_information"]
    assert response.json["status"], "success"
    assert response.status_code == 201

    response = client.post(
        "/add-data-block/",
        json={
            "block_type": "cycle",
            "item_id": default_starting_material_dict["item_id"],
            "index": 0,
        },
    )

    assert response.status_code == 200
    response_json = response.json
    assert response_json["status"] == "success"
    assert response_json["new_block_obj"]
    block_id = response_json["new_block_obj"]["block_id"]
    assert block_id
    assert response_json["new_block_insert_index"] == 0

    response = client.post(
        "/delete-block/",
        json={"item_id": default_starting_material_dict["item_id"], "block_id": block_id},
    )
    assert response.status_code == 200

    # Check that a normal user cannot entirely delete a starting material that has no user
    response = client.post(
        "/delete-sample/",
        json={"item_id": default_starting_material_dict["item_id"]},
    )

    assert response.status_code == 401

    # Check that the admin can delete a starting material that has no user
    response = admin_client.post(
        "/delete-sample/",
        json={"item_id": default_starting_material_dict["item_id"]},
    )
    assert response.status_code == 200
