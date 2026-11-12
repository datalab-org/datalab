"""More item graph tests (in addition to `test_graph.py`) that
are written to be more isolated from one another.

"""

import json

import pytest

from pydatalab.models import Cell, Sample, StartingMaterial


def _create_item(client, item):
    response = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(item.model_dump_json())},
    )
    assert response.status_code == 201, response.json


def _get_item_data(client, item_id):
    response = client.get(f"/get-item-data/{item_id}")
    assert response.status_code == 200, response.json
    return response.json["item_data"]


def _save_item(client, item_id, data):
    response = client.post("/save-item/", json={"item_id": item_id, "data": data})
    assert response.status_code == 200, response.json


def _graph_edges(client, item_id):
    graph = client.get(f"/item-graph/{item_id}").json
    return {(edge["data"]["source"], edge["data"]["target"]) for edge in graph["edges"]}


def _related_item_ids(item_data):
    return {rel.get("item_id") for rel in item_data["relationships"] if rel.get("item_id")}


def test_single_starting_material(admin_client, client):
    item_id = "material"

    material = StartingMaterial(item_id=item_id)

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(material.model_dump_json())},
    )

    assert creation.status_code == 201

    # A single material without connections should be ignored
    graph = client.get("/item-graph").json
    assert len(graph["nodes"]) == 0

    # Unless it is asked for directly
    graph = client.get(f"/item-graph/{item_id}").json
    assert len(graph["nodes"]) == 1

    # Now make a sample and connect it to the starting material; check that the
    # starting material is now shown by default
    parent = Sample(
        item_id="parent",
        synthesis_constituents=[
            {"item": {"item_id": item_id, "type": "starting_materials"}, "quantity": None}
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(parent.model_dump_json())},
    )

    assert creation.status_code == 201

    graph = client.get("/item-graph").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    # From both the starting material and the sample
    graph = client.get(f"/item-graph/{item_id}").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    # From both the starting material and the sample
    graph = client.get("/item-graph/parent").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    # Now add a few more samples in a chain and check that only the relevant ones are shown
    child = Sample(
        item_id="child",
        synthesis_constituents=[
            {"item": {"item_id": "parent", "type": "samples"}, "quantity": None}
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(child.model_dump_json())},
    )

    grandchild = Sample(
        item_id="grandchild",
        synthesis_constituents=[
            {"item": {"item_id": "child", "type": "samples"}, "quantity": None}
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(grandchild.model_dump_json())},
    )

    great_grandchild = Sample(
        item_id="great-grandchild",
        synthesis_constituents=[
            {"item": {"item_id": "grandchild", "type": "samples"}, "quantity": None}
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(great_grandchild.model_dump_json())},
    )

    graph = client.get("/item-graph").json
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4

    # Check for bug where this behaviour was inconsistent between admin and non-admin users
    # Admin needs ?sudo=1 to see items not created by them (super-user mode)
    graph = admin_client.get("/item-graph/great-grandchild?sudo=1").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    # Add an admin only item and check that the non-admin user still sees the same graph
    admin_great_great_grandchild = Sample(
        item_id="admin-great-great-grandchild",
        synthesis_constituents=[
            {"item": {"item_id": "great-grandchild", "type": "samples"}, "quantity": None}
        ],
    )

    creation = admin_client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(admin_great_great_grandchild.model_dump_json())},
    )

    graph = admin_client.get("/item-graph/great-grandchild?sudo=1").json
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2

    graph = client.get("/item-graph/great-grandchild").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    # Put node in a collection and see if its shown
    response = admin_client.put(
        "/collections",
        json={
            "data": {
                "collection_id": "test-collection",
                "starting_members": [{"item_id": "great-grandchild"}],
            }
        },
    )
    assert response.status_code == 201

    client_collection_graph = client.get("/item-graph?collection_id=test-collection").json
    assert client_collection_graph["status"] == "error"

    collection_graph = admin_client.get("/item-graph?collection_id=test-collection&sudo=1").json
    assert len(collection_graph["nodes"]) == 1
    assert len(collection_graph["edges"]) == 0

    graph = client.get("/item-graph/great-grandchild?hide_collections=false").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    admin_graph = admin_client.get(
        "/item-graph/great-grandchild?hide_collections=false&sudo=1"
    ).json
    assert len(admin_graph["nodes"]) == 4
    assert len(admin_graph["edges"]) == 3


@pytest.mark.parametrize("send_collections", [True, False])
def test_removed_synthesis_constituent_detached_from_graph(client, send_collections):
    """Removing a synthesis constituent via `/save-item/` should remove the
    corresponding relationship and graph edge, whether or not the client sends
    the `collections` field (the webapp does, other API clients may not).

    See https://github.com/datalab-org/datalab/issues/395.

    """
    suffix = "with-colls" if send_collections else "without-colls"
    material_ids = [f"detach-sm-1-{suffix}", f"detach-sm-2-{suffix}", f"detach-sm-3-{suffix}"]
    sample_id = f"detach-sample-{suffix}"

    for material_id in material_ids:
        _create_item(client, StartingMaterial(item_id=material_id))

    _create_item(
        client,
        Sample(
            item_id=sample_id,
            synthesis_constituents=[
                {"item": {"item_id": material_id, "type": "starting_materials"}, "quantity": None}
                for material_id in material_ids[:2]
            ],
        ),
    )

    assert _graph_edges(client, sample_id) == {(m, sample_id) for m in material_ids[:2]}

    # Swap the second constituent for the third
    data = _get_item_data(client, sample_id)
    if not send_collections:
        data.pop("collections")
    data["synthesis_constituents"] = [
        c for c in data["synthesis_constituents"] if c["item"]["item_id"] != material_ids[1]
    ] + [{"item": {"item_id": material_ids[2], "type": "starting_materials"}, "quantity": None}]
    _save_item(client, sample_id, data)

    related = _related_item_ids(_get_item_data(client, sample_id))
    assert material_ids[1] not in related
    assert {material_ids[0], material_ids[2]} <= related

    assert _graph_edges(client, sample_id) == {
        (material_ids[0], sample_id),
        (material_ids[2], sample_id),
    }
    assert _graph_edges(client, material_ids[1]) == set()


@pytest.mark.parametrize("send_collections", [True, False])
def test_removed_cell_component_detached_from_graph(client, send_collections):
    """Removing an electrode/electrolyte constituent from a cell via `/save-item/`
    should remove the corresponding relationship and graph edge.

    See https://github.com/datalab-org/datalab/issues/395.

    """
    suffix = "with-colls" if send_collections else "without-colls"
    cathode_id = f"detach-cathode-{suffix}"
    anode_id = f"detach-anode-{suffix}"
    electrolyte_id = f"detach-electrolyte-{suffix}"
    cell_id = f"detach-cell-{suffix}"

    for material_id in (cathode_id, anode_id, electrolyte_id):
        _create_item(client, StartingMaterial(item_id=material_id))

    def component(item_id):
        return [{"item": {"item_id": item_id, "type": "starting_materials"}, "quantity": None}]

    _create_item(
        client,
        Cell(
            item_id=cell_id,
            positive_electrode=component(cathode_id),
            negative_electrode=component(anode_id),
            electrolyte=component(electrolyte_id),
        ),
    )

    assert _graph_edges(client, cell_id) == {
        (cathode_id, cell_id),
        (anode_id, cell_id),
        (electrolyte_id, cell_id),
    }

    # Detach the anode and the electrolyte
    data = _get_item_data(client, cell_id)
    if not send_collections:
        data.pop("collections")
    data["negative_electrode"] = []
    data["electrolyte"] = []
    _save_item(client, cell_id, data)

    related = _related_item_ids(_get_item_data(client, cell_id))
    assert cathode_id in related
    assert anode_id not in related
    assert electrolyte_id not in related

    assert _graph_edges(client, cell_id) == {(cathode_id, cell_id)}
    assert _graph_edges(client, anode_id) == set()
    assert _graph_edges(client, electrolyte_id) == set()
