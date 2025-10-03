import json

from pydatalab.models import Cell, Sample
from pydatalab.models.utils import Constituent


def test_simple_graph(admin_client):
    """Test the graph API with a simple manually constructed graph.
    All samples are uploaded without a creator so the test client needs admin priveleges.

    """
    parent = Sample(
        item_id="parent",
    )

    child_1 = Sample(
        item_id="child_1",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent"}, quantity=None),
        ],
    )

    child_2 = Sample(
        item_id="child_2",
        refcode="test:TEST02",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent"}, quantity=None),
        ],
    )

    child_3 = Sample(
        item_id="child_3",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent"}, quantity=None),
        ],
    )

    child_4 = Sample(
        item_id="child_4",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent"}, quantity=None),
        ],
    )

    missing_child = Sample(
        item_id="missing_child",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent"}, quantity=None),
        ],
    )

    cell = Cell(
        item_id="abcd-1-2-3",
        positive_electrode=[{"item": parent, "quantity": 2}],
        negative_electrode=[
            {"item": {"name": "My secret cathode", "chemform": "NaCoO2"}, "quantity": 3}
        ],
        characteristic_mass=1.2,
        active_ion="Na+",
        cell_format="swagelok",
    )

    new_samples = [
        json.loads(d.json())
        for d in [parent, child_1, child_2, child_3, child_4, missing_child, cell]
    ]

    sample_list = admin_client.post(
        "/new-samples/",
        json={"new_sample_datas": new_samples},
    )

    assert sample_list.status_code == 207
    assert all(d == 201 for d in sample_list.json["http_codes"])

    graph = admin_client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "child_3",
        "child_4",
        "missing_child",
        "abcd-1-2-3",
    }
    assert len(graph["edges"]) == 6

    response = admin_client.post("/delete-sample/", json={"item_id": "missing_child"})
    assert response

    graph = admin_client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "child_3",
        "child_4",
        "abcd-1-2-3",
    }

    assert len(graph["edges"]) == 5

    graph = admin_client.get("/item-graph/child_1").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    graph = admin_client.get("/item-graph/parent").json
    assert len(graph["nodes"]) == 6
    assert len(graph["edges"]) == 5

    collection_id = "testcoll"
    collection_json = {
        "data": {
            "collection_id": collection_id,
            "title": "Test title",
            "starting_members": [
                {"item_id": "parent"},
                {"item_id": "child_1"},
                {"item_id": "child_2"},
            ],
        }
    }
    response = admin_client.put("/collections", json=collection_json)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    graph = admin_client.get(f"/item-graph?collection_id={collection_id}").json
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2

    graph = admin_client.get("/item-graph/parent").json
    assert len(graph["nodes"]) == 6
    assert len(graph["edges"]) == 5

    samples = sample_list.json["responses"]

    refcode_child_3 = None
    refcode_child_4 = None

    for item in samples:
        if item["item_id"] == "child_3":
            refcode_child_3 = item["sample_list_entry"].get("refcode")
        elif item["item_id"] == "child_4":
            refcode_child_4 = item["sample_list_entry"].get("refcode")

    response = admin_client.post(
        f"/collections/{collection_id}",
        json={"data": {"refcodes": [refcode_child_3, refcode_child_4]}},
    )

    assert response.status_code == 200
    assert response.json["status"] == "success"

    graph = admin_client.get(f"/item-graph?collection_id={collection_id}").json
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4

    graph = admin_client.get("/item-graph/parent").json
    assert len(graph["nodes"]) == 6
    assert len(graph["edges"]) == 5


def test_delete_item_cleans_relationships_and_constituents(admin_client):
    """Test that deleting an item removes relationships and transforms synthesis_constituents to inline."""

    parent = Sample(item_id="parent_to_delete", name="Test Parent", chemform="NaCl")
    response = admin_client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(parent.json())},
    )
    assert response.status_code == 201

    child = Sample(
        item_id="child_with_constituent",
        synthesis_constituents=[
            Constituent(item={"type": "samples", "item_id": "parent_to_delete"}, quantity=5.0)
        ],
    )
    response = admin_client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(child.json())},
    )
    assert response.status_code == 201

    response = admin_client.get("/get-item-data/child_with_constituent")
    assert response.status_code == 200
    assert "parent_to_delete" in response.json["parent_items"]
    relationships = response.json["item_data"]["relationships"]
    assert any(r.get("item_id") == "parent_to_delete" for r in relationships)

    constituents = response.json["item_data"]["synthesis_constituents"]
    assert len(constituents) == 1
    assert constituents[0]["item"]["item_id"] == "parent_to_delete"
    assert constituents[0]["item"]["type"] == "samples"

    response = admin_client.post("/delete-sample/", json={"item_id": "parent_to_delete"})
    assert response.status_code == 200

    response = admin_client.get("/get-item-data/child_with_constituent")
    assert response.status_code == 200
    assert "parent_to_delete" not in response.json["parent_items"]
    relationships = response.json["item_data"]["relationships"]
    assert not any(r.get("item_id") == "parent_to_delete" for r in relationships)

    constituents = response.json["item_data"]["synthesis_constituents"]
    assert len(constituents) == 1
    constituent_item = constituents[0]["item"]
    assert constituent_item["name"] == "Test Parent"
    assert constituent_item["chemform"] == "NaCl"
    assert "item_id" not in constituent_item
    assert "refcode" not in constituent_item
    assert "type" not in constituent_item
    assert "immutable_id" not in constituent_item

    graph = admin_client.get("/item-graph/child_with_constituent").json
    assert graph["status"] == "success"
    assert len(graph["nodes"]) == 1
    assert graph["nodes"][0]["data"]["id"] == "child_with_constituent"
