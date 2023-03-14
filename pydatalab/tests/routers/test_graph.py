import json

from pydatalab.models import Cell, Sample
from pydatalab.models.samples import Constituent


def test_simple_graph(client):

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
            {"item": {"name": "My secret cathode", "formula": "NaCoO2"}, "quantity": 3}
        ],
        characteristic_mass=1.2,
        active_ion="Na+",
        cell_format="swagelok",
    )

    new_samples = [json.loads(d.json()) for d in [parent, child_1, child_2, missing_child, cell]]

    response = client.post(
        "/new-samples/",
        json={"new_sample_datas": new_samples},
    )

    assert response.status_code == 207
    assert all(d == 201 for d in response.json["http_codes"])

    graph = client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "missing_child",
        "abcd-1-2-3",
    }
    assert len(graph["edges"]) == 4

    response = client.post("/delete-sample/", json={"item_id": "missing_child"})
    assert response

    graph = client.get("/item-graph").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "abcd-1-2-3",
    }

    assert len(graph["edges"]) == 3
