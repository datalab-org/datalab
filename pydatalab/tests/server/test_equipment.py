import datetime

import pytest


@pytest.mark.dependency()
def test_empty_equipment(client):
    response = client.get("/equipment/")
    assert len(response.json["items"]) == 0
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_empty_equipment"])
def test_new_equipment(client, default_equipment_dict):
    print(default_equipment_dict)
    response = client.post("/new-sample/", json=default_equipment_dict)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    print(response.json["sample_list_entry"])

    # all equipment should have no creators currently (they are shared among a deployment):
    assert len(response.json["sample_list_entry"]["creators"]) == 0

    for key, value in response.json["sample_list_entry"].items():
        if key in default_equipment_dict:
            if isinstance(v := default_equipment_dict[key], datetime.datetime):
                v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
            assert value == v


@pytest.mark.dependency(depends=["test_new_equipment"])
def test_get_item_data(client, default_equipment_dict):
    response = client.get("/get-item-data/test_e1")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # all equipment should have no creators currently (they are shared among a deployment):
    assert len(response.json["item_data"]["creators"]) == 0
    assert len(response.json["item_data"]["creator_ids"]) == 0

    for key in default_equipment_dict:
        if isinstance(v := default_equipment_dict[key], datetime.datetime):
            v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_equipment", "test_get_item_data"])
def test_new_equipment_with_automatically_generated_id(client):
    new_equipment_data = {
        "name": "equipment with random id",
        "date": datetime.datetime.fromisoformat("1995-03-02"),
        "type": "equipment",
    }

    request_json = dict(
        new_sample_data=new_equipment_data,
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

    for key in new_equipment_data:
        if isinstance(v := new_equipment_data[key], datetime.datetime):
            v = v.replace(tzinfo=datetime.timezone.utc).isoformat()
        assert response.json["item_data"][key] == v


@pytest.mark.dependency(depends=["test_new_equipment"])
def test_new_equipment_collision(client, default_equipment_dict):
    # Try to do the same thing again, expecting an ID collision
    response = client.post("/new-sample/", json=default_equipment_dict)
    # Test that 409: Conflict is returned
    assert response.status_code == 409


@pytest.mark.dependency(depends=["test_new_equipment"])
def test_save_good_equipment(client, default_equipment_dict):
    updated_equipment = default_equipment_dict.copy()
    updated_equipment.update({"description": "This is a newer test sample."})
    response = client.post(
        "/save-item/",
        json={
            "item_id": default_equipment_dict["item_id"],
            "data": updated_equipment,
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"

    response = client.get("/get-item-data/test_e1")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_equipment_dict:
        if key in updated_equipment and key in response.json:
            assert response.json[key] == updated_equipment[key]


def test_get_equipment_summary_naive_datetime_serialized_as_utc(client, database):
    """Regression test for `CustomJSONEncoder`/`BSONProvider`: MongoDB has no
    timezone concept (BSON dates are plain UTC instants), so `pymongo.MongoClient`
    (not configured with `tz_aware=True`) always reads dates back as *naive*
    Python datetimes -- with no intervening Pydantic validation, e.g. via
    `get_equipment_summary`'s raw aggregation -- regardless of whether the value
    was originally written as tz-aware. The encoder must assume UTC for such
    naive datetimes before calling `.isoformat()`, otherwise the serialized
    string carries no timezone offset and clients (e.g. JS `Date` parsing)
    misinterpret it as local time.
    """
    aware_date = datetime.datetime(2026, 7, 15, 14, 30, 0, 123000, tzinfo=datetime.timezone.utc)

    database.items.insert_one(
        {
            "item_id": "test_naive_datetime_equipment",
            "type": "equipment",
            "date": aware_date,
            "refcode": "test:NAIVEDATETIME",
            "status": None,
        }
    )

    try:
        # Confirm the premise: pymongo hands back a naive datetime even though
        # `aware_date` was tz-aware when written.
        raw_doc = database.items.find_one({"item_id": "test_naive_datetime_equipment"})
        assert raw_doc["date"].tzinfo is None

        response = client.get("/equipment/")
        assert response.status_code == 200

        entry = next(
            item
            for item in response.json["items"]
            if item["item_id"] == "test_naive_datetime_equipment"
        )
        # The serialized date must carry an explicit UTC offset/designator, matching
        # the original tz-aware value.
        assert entry["date"] == aware_date.isoformat()
    finally:
        database.items.delete_one({"item_id": "test_naive_datetime_equipment"})


@pytest.mark.dependency(depends=["test_new_equipment"])
def test_delete_equipment(admin_client, default_equipment_dict):
    """For now, only admins can delete equipment."""
    response = admin_client.post(
        "/delete-sample/",
        json={"item_id": default_equipment_dict["item_id"]},
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # Check it was actually deleted
    response = admin_client.get(
        f"/get-item-data/{default_equipment_dict['item_id']}",
    )
    assert response.status_code == 404
