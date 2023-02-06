import datetime
import json

import pytest

from pydatalab.models import Sample
from pydatalab.models.relationships import RelationshipType, TypedRelationship


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
    assert response.status_code == 200
    response = client.get(f"/get-item-data/{default_sample_dict['item_id']}")
    assert "unknown_key" not in response.json["item_data"]


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
    assert response.status_code == 401


@pytest.mark.dependency(depends=["test_delete_sample"])
def test_create_indices(real_mongo_client):
    from pydatalab.mongo import create_default_indices

    if real_mongo_client is None:
        pytest.skip("Skipping FTS tests, not connected to real MongoDB")

    create_default_indices(real_mongo_client)
    indexes = list(real_mongo_client.get_database().items.list_indexes())
    expected_index_names = ("_id_", "items full-text search", "item type", "unique item ID")
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
    assert len(response.json["items"]) == 2
    assert response.json["items"][0]["item_id"] == "12345"
    assert response.json["items"][1]["item_id"] == "sample_1"

    response = client.get("/search-items/?query=new material")

    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert len(response.json["items"]) == 2
    assert response.json["items"][0]["item_id"] == "material"
    assert response.json["items"][1]["item_id"] == "12345"

    response = client.get("/search-items/?query=NaNiO2")

    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert len(response.json["items"]) == 3
    assert response.json["items"][0]["item_id"] == "test"
    assert response.json["items"][1]["item_id"] == "material"
    assert response.json["items"][2]["item_id"] == "12345"


@pytest.mark.dependency(depends=["test_delete_sample"])
def test_new_sample_with_relationships(client, complicated_sample):

    complicated_sample_json = json.loads(complicated_sample.json())
    response = client.post("/new-sample/", json=complicated_sample_json)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    assert response.json["sample_list_entry"]["item_id"] == complicated_sample.item_id

    response = client.get(
        f"/get-item-data/{complicated_sample.item_id}",
    )

    assert response.json["parent_items"] == [
        "starting_material_1",
        "starting_material_2",
        "starting_material_3",
    ]
    assert response.json["child_items"] == []
    assert [d["item_id"] for d in response.json["item_data"]["relationships"]] == [
        "starting_material_1",
        "starting_material_2",
        "starting_material_3",
    ]
    assert len(response.json["item_data"]["relationships"]) == 3
    assert len(response.json["item_data"]["synthesis_constituents"]) == 3

    # Create a derived sample with new relationships and make sure they are properly interleaved
    derived_sample = Sample(**response.json["item_data"])
    derived_sample.item_id = "derived_sample"

    # Remove one constituent ('starting_material_3') and check it
    # is also removed from the relationships
    derived_sample.synthesis_constituents = [
        d for d in derived_sample.synthesis_constituents if d.item.item_id != "starting_material_3"
    ]
    derived_sample.relationships.append(
        TypedRelationship(
            relation=RelationshipType.SIBLING,
            item_id=complicated_sample.item_id,
            type=complicated_sample.type,
        )
    )
    derived_sample.relationships.append(
        TypedRelationship(
            relation=RelationshipType.OTHER,
            item_id="starting_material_1",
            type="starting_materials",
            description="This is a new relationship",
        )
    )
    derived_sample_json = json.loads(derived_sample.json())

    response = client.post("/new-sample/", json=derived_sample_json)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["sample_list_entry"]["item_id"] == derived_sample.item_id

    response = client.get(
        f"/get-item-data/{derived_sample.item_id}",
    )

    assert len(response.json["item_data"]["synthesis_constituents"]) == 2
    assert response.json["parent_items"] == [
        "starting_material_1",
        "starting_material_2",
        # i.e., "starting_material_3", has been removed
    ]
    assert response.json["child_items"] == []
    assert [d["item_id"] for d in response.json["item_data"]["relationships"]] == [
        "starting_material_1",
        "starting_material_2",
        complicated_sample.item_id,
        "starting_material_1",
        # i.e., "starting_material_3", has been removed
    ]


@pytest.mark.dependency(depends=["test_new_sample_with_relationships"])
def test_saved_sample_has_new_relationships(client, default_sample_dict, complicated_sample):
    """Create a sample, add a constituent and save it, then make sure
    it appears in relationship searches, without manually using the Sample
    model to populate them.

    """

    default_sample_dict["item_id"] = "debug"
    response = client.post("/new-sample/", json=default_sample_dict)

    assert response.json

    response = client.get(
        f"/get-item-data/{default_sample_dict['item_id']}",
    )

    assert response.json

    sample_dict = response.json["item_data"]
    sample_dict["synthesis_constituents"] = [
        {
            "item": {"item_id": complicated_sample.item_id, "type": "samples"},
            "quantity": 25.2,
            "unit": "g",
        }
    ]

    response = client.post(
        "/save-item/", json={"item_id": sample_dict["item_id"], "data": sample_dict}
    )

    # Saving this link *should* add a searchable relationship in the database on both the new and old sample
    response = client.get(
        f"/get-item-data/{default_sample_dict['item_id']}",
    )
    assert complicated_sample.item_id in response.json["parent_items"]

    response = client.get(
        f"/get-item-data/{complicated_sample.item_id}",
    )
    assert sample_dict["item_id"] in response.json["child_items"]


@pytest.mark.dependency(depends=["test_saved_sample_has_new_relationships"])
def test_copy_from_sample(client, complicated_sample):
    """Create a sample, add a constituent and save it, then create a new
    sample that copies from the old, potentially adding another consituent.

    """
    complicated_sample.item_id = "new_complicated_sample"
    complicated_sample_json = json.loads(complicated_sample.json())
    response = client.post("/new-sample/", json=complicated_sample_json)

    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    # Now try to directly make a copy that has the same data with a new ID
    copy_doc = {"item_id": "copy_of_complicated_sample"}
    copy_request = {"new_sample_data": copy_doc, "copy_from_item_id": complicated_sample.item_id}
    response = client.post("/new-sample/", json=copy_request)

    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    copy_doc = {"item_id": "copy_of_complicated_sample"}

    response = client.get(
        f"/get-item-data/{copy_doc['item_id']}",
    )

    assert response.json["parent_items"] == [
        "starting_material_1",
        "starting_material_2",
        "starting_material_3",
    ]
