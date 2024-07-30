import copy
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
        if key == "creator_ids":
            continue
        if isinstance(v := default_sample_dict[key], datetime.datetime):
            v = v.isoformat()
        assert response.json["sample_list_entry"][key] == v


@pytest.mark.dependency(depends=["test_new_sample"])
def test_get_item_data(client, default_sample_dict):
    response = client.get("/get-item-data/12345")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in default_sample_dict.keys():
        if key == "creator_ids":
            continue
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


@pytest.mark.dependency(depends=["test_new_sample", "test_get_item_data"])
def test_new_sample_with_automatically_generated_id(client, user_id):
    new_sample_data = {
        "name": "sample with random id",
        "date": datetime.datetime.fromisoformat("1995-03-02"),
        "chemform": "H2O",
        "type": "samples",
        "synthesis_description": "2 parts hydrogen were added to 1 part oxygen",
        "creator_ids": [user_id],
    }

    request_json = dict(
        new_sample_data=new_sample_data,
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

    for key in new_sample_data.keys():
        if isinstance(v := new_sample_data[key], datetime.datetime):
            v = v.isoformat()
        if key == "creator_ids":
            continue
        assert response.json["item_data"][key] == v


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
    assert response.status_code == 404


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

    response = client.get("/search-items/?query='grey:TEST4'")

    assert response.status_code == 200
    assert response.json["status"] == "success"
    # should return all grey:TEST<n> samples, with TEST4 first
    assert len(response.json["items"]) == 5
    assert response.json["items"][0]["item_id"] == "material"


@pytest.mark.dependency(depends=["test_delete_sample"])
def test_new_sample_with_relationships(client, complicated_sample):
    complicated_sample_json = json.loads(complicated_sample.json())
    response = client.post("/new-sample/", json=complicated_sample_json)
    # Test that 201: Created is emitted
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    new_refcode = response.json["sample_list_entry"]["refcode"]
    assert new_refcode.startswith("test:")
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
            refcode=new_refcode,
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
    assert [d.get("item_id") for d in response.json["item_data"]["relationships"]] == [
        "starting_material_1",
        "starting_material_2",
        None,
        "starting_material_1",
        # i.e., "starting_material_3", has been removed
    ]

    assert [d.get("refcode") for d in response.json["item_data"]["relationships"]] == [
        None,
        None,
        new_refcode,
        None,
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
    new_refcode = response.json["item_data"]["refcode"]
    assert new_refcode.startswith("test:")

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


@pytest.mark.dependency(depends=["test_copy_from_sample"])
def test_create_multiple_samples(client, complicated_sample):
    samples = [complicated_sample, complicated_sample.copy()]
    samples[0].item_id = "another_new_complicated_sample"
    samples[1].item_id = "additional_new_complicated_sample"

    response = client.post(
        "/new-samples/", json={"new_sample_datas": [json.loads(s.json()) for s in samples]}
    )
    assert response.status_code == 207, response.json
    assert response.json["nsuccess"] == 2, response.json
    assert response.json["nerror"] == 0

    samples = [
        Sample(item_id="one_more_new_complicated_sample"),
        Sample(item_id="and_again_new_complicated_sample"),
    ]

    response = client.post(
        "/new-samples/",
        json={
            "new_sample_datas": [json.loads(s.json()) for s in samples],
            "copy_from_item_ids": [
                "another_new_complicated_sample",
                "additional_new_complicated_sample",
            ],
        },
    )

    assert response.status_code == 207, response.json
    assert response.json["nsuccess"] == 2
    assert response.json["nerror"] == 0

    response = client.get("/get-item-data/one_more_new_complicated_sample")
    assert response.status_code == 200
    assert (
        response.json["item_data"]["synthesis_constituents"][0]["item"]["item_id"]
        == "starting_material_1"
    )


@pytest.mark.dependency(depends=["test_create_multiple_samples"])
def test_create_cell(client, default_cell):
    response = client.post("/new-sample/", json=json.loads(default_cell.json()))
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    test_id = "copy_of_complicated_cell"

    copy_doc = {
        "item_id": test_id,
        "type": "cells",
        "electrolyte": [
            {"item": {"name": "salt", "chemform": "NaCl"}, "quantity": 100, "unit": "ml"}
        ],
    }
    copy_request = {"new_sample_data": copy_doc, "copy_from_item_id": default_cell.item_id}
    response = client.post("/new-sample/", json=copy_request)
    # Check that the copy retains the old components and the new
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    response = client.get(f"/get-item-data/{test_id}")
    cell = response.json["item_data"]
    assert cell["electrolyte"][0]["item"]["name"] == "inlined reference"
    assert cell["electrolyte"][1]["item"]["name"] == "salt"
    assert cell["electrolyte"][1]["item"]["chemform"] == "NaCl"

    assert (
        cell["positive_electrode"][0]["item"]["name"]
        == default_cell.positive_electrode[0].item.name
    )
    assert (
        cell["negative_electrode"][0]["item"]["name"]
        == default_cell.negative_electrode[0].item.name
    )


@pytest.mark.dependency(depends=["test_create_cell"])
def test_cell_from_scratch(client):
    cell = {
        "item_id": "test_cell_from_scratch",
        "type": "cells",
        "negative_electrode": [{"quantity": None, "item": {"name": "inline test"}}],
    }

    response = client.post("/new-sample/", json=cell)
    assert response.status_code == 201

    # copy a cell with additional components, where previously there were none
    copy_id = "copy_of_scratch"
    cell.update(
        {
            "item_id": copy_id,
            "positive_electrode": [{"quantity": None, "item": {"name": "inline cathode"}}],
        }
    )
    response = client.post(
        "/new-sample/",
        json={"new_sample_data": cell, "copy_from_item_id": "test_cell_from_scratch"},
    )
    assert response.status_code == 201

    response = client.get(f"/get-item-data/{copy_id}")
    new_cell = response.json["item_data"]
    assert new_cell["negative_electrode"][0]["item"]["name"] == "inline test"
    assert new_cell["positive_electrode"][0]["item"]["name"] == "inline cathode"


@pytest.mark.dependency(depends=["test_create_cell"])
def test_create_collections(client, default_collection):
    # Check no collections initially
    response = client.get("/collections")
    assert len(response.json["data"]) == 0, response.json
    assert response.status_code == 200

    # Create an empty collection
    response = client.put("/collections", json={"data": json.loads(default_collection.json())})
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["data"]["collection_id"] == "test_collection"
    assert response.json["data"]["title"] == "My Test Collection"
    assert response.json["data"]["num_items"] == 0

    response = client.get("/collections")
    assert response.status_code == 200
    assert len(response.json["data"]) == 1
    assert response.json["data"][0]["collection_id"] == "test_collection"
    assert response.json["data"][0]["title"] == "My Test Collection"
    assert response.status_code == 200

    # Create a collection with initial items
    new_collection = copy.deepcopy(default_collection)
    new_collection.collection_id = "test_collection_2"

    data = json.loads(new_collection.json())
    data.update(
        {
            "starting_members": [
                {"item_id": "copy_of_complicated_cell"},
                {"item_id": "test_cell"},
            ]
        }
    )
    response = client.put("/collections", json={"data": data})
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["data"]["collection_id"] == "test_collection_2"
    assert response.json["data"]["title"] == "My Test Collection"
    assert response.json["data"]["num_items"] == 2
    response = client.get(f"/collections/{new_collection.collection_id}")
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"
    assert response.json["collection_id"] == "test_collection_2"
    assert response.json["data"]["collection_id"] == "test_collection_2"
    assert response.json["data"]["title"] == "My Test Collection"
    assert response.json["data"]["num_items"] == 2
    ids = {doc["item_id"] for doc in response.json["child_items"]}
    assert ids == {"copy_of_complicated_cell", "test_cell"}
    test_id = ids.pop()
    response = client.get(f"/get-item-data/{test_id}")
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"
    assert len(response.json["item_data"]["collections"]) == 1
    assert response.json["item_data"]["collections"][0]["collection_id"] == "test_collection_2"

    # Test that collections can be deleted and relationships to items are removed
    response = client.delete(f"/collections/{new_collection.collection_id}")
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"
    response = client.get(f"/collections/{new_collection.collection_id}")
    assert response.status_code == 404, response.json
    test_id = ids.pop()
    response = client.get(f"/get-item-data/{test_id}")
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"
    assert len(response.json["item_data"]["collections"]) == 0

    # remake it for the next test
    response = client.put("/collections", json={"data": data})
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["data"]["collection_id"] == "test_collection_2"
    assert response.json["data"]["title"] == "My Test Collection"
    assert response.json["data"]["num_items"] == 2


@pytest.mark.dependency(depends=["test_create_collections"])
def test_items_added_to_existing_collection(client, default_collection, default_sample_dict):
    # Create a new item that is inside the default collection by passing collection_id
    new_id = "testing_collection_insert_by_id"
    default_sample_dict["item_id"] = new_id
    default_sample_dict["collections"] = [{"collection_id": default_collection.collection_id}]
    response = client.post("/new-sample/", json=default_sample_dict)
    assert response.status_code == 201, response.json
    response = client.get(f"/collections/{default_collection.collection_id}")
    assert response.status_code == 200, response.json
    collection_immutable_id = response.json["data"]["immutable_id"]
    assert new_id in [d["item_id"] for d in response.json["child_items"]]

    # Make sure that a new item that is inside a non-existent collection gives an error
    new_id = "testing_collection_insert_by_id_2"
    default_sample_dict["item_id"] = new_id
    default_sample_dict["collections"] = [{"collection_id": "random_id"}]
    response = client.post("/new-sample/", json=default_sample_dict)
    assert response.status_code == 401, response.json
    response = client.get(f"/get-item-data/{new_id}")
    assert response.status_code == 404, response.json

    # Create a new item that is inside the default collection by passing immutable id
    new_id2 = "testing_collection_insert_by_immutable"
    default_sample_dict["item_id"] = new_id2
    default_sample_dict["collections"] = [{"immutable_id": collection_immutable_id}]
    response = client.post("/new-sample/", json=default_sample_dict)
    assert response.status_code == 201, response.json
    response = client.get(f"/collections/{default_collection.collection_id}")
    assert response.status_code == 200, response.json
    assert new_id2 in [d["item_id"] for d in response.json["child_items"]]

    # Update an existing item with membership of an existing collection
    default_sample_dict["item_id"] = new_id2
    default_sample_dict["collections"] = [
        {"immutable_id": collection_immutable_id},
        {"collection_id": "test_collection_2"},
    ]
    response = client.post("/save-item/", json={"data": default_sample_dict, "item_id": new_id2})
    assert response.status_code == 200, response.json

    response = client.get(f"/get-item-data/{new_id2}")
    assert response.status_code == 200, response.json
    assert "test_collection_2" in [
        d["collection_id"] for d in response.json["item_data"]["collections"]
    ]
    assert default_collection.collection_id in [
        d["collection_id"] for d in response.json["item_data"]["collections"]
    ]

    # Update an existing item with deleted membership of an existing collection
    default_sample_dict["item_id"] = new_id2
    default_sample_dict["collections"] = [
        {"collection_id": "test_collection_2"},
    ]
    response = client.post("/save-item/", json={"data": default_sample_dict, "item_id": new_id2})
    assert response.status_code == 200, response.json

    response = client.get(f"/get-item-data/{new_id2}")
    assert response.status_code == 200, response.json
    assert "test_collection_2" in [
        d["collection_id"] for d in response.json["item_data"]["collections"]
    ]
    assert default_collection.collection_id not in [
        d["collection_id"] for d in response.json["item_data"]["collections"]
    ]

    # Update an existing item with a non-existent collection
    default_sample_dict["item_id"] = new_id2
    default_sample_dict["collections"] = [
        {"collection_id": "test_collection_3"},
    ]
    response = client.post("/save-item/", json={"data": default_sample_dict, "item_id": new_id2})
    assert response.status_code == 401, response.json

    # Check that sending same collection multiple times doesn't lead to duplicates
    default_sample_dict["item_id"] = new_id2
    default_sample_dict["collections"] = [
        {"collection_id": "test_collection_2"},
    ]
    response = client.post("/save-item/", json={"data": default_sample_dict, "item_id": new_id2})
    assert response.status_code == 200, response.json

    response = client.get(f"/get-item-data/{new_id2}")
    assert response.status_code == 200, response.json
    assert "test_collection_2" in [
        d["collection_id"] for d in response.json["item_data"]["collections"]
    ]
    assert len(response.json["item_data"]["collections"]) == 1
    assert (
        len([d for d in response.json["item_data"]["relationships"] if d["type"] == "collections"])
        == 1
    )
