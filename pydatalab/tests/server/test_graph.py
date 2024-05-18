import json

from pydatalab.models import Cell, Sample
from pydatalab.models.samples import Constituent


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

    new_samples = [json.loads(d.json()) for d in [parent, child_1, child_2, missing_child, cell]]

    response = admin_client.post(
        "/new-samples/",
        json={"new_sample_datas": new_samples},
    )

    assert response.status_code == 207
    assert all(d == 201 for d in response.json["http_codes"])

    graph = admin_client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "missing_child",
        "abcd-1-2-3",
    }
    assert len(graph["edges"]) == 4

    response = admin_client.post("/delete-sample/", json={"item_id": "missing_child"})
    assert response

    graph = admin_client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "abcd-1-2-3",
    }

    assert len(graph["edges"]) == 3

    graph = admin_client.get("/item-graph/child_1").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    graph = admin_client.get("/item-graph/parent").json
    assert len(graph["nodes"]) == 4
    assert len(graph["edges"]) == 3

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
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 8
