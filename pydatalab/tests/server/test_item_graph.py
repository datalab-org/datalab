"""More item graph tests (in addition to `test_graph.py`) that
are written to be more isolated from one another.

"""

import json

from pydatalab.models import Sample, StartingMaterial


def test_single_starting_material(admin_client):
    item_id = "material"

    material = StartingMaterial(item_id=item_id)

    creation = admin_client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(material.json())},
    )

    assert creation.status_code == 201

    # A single material without connections should be ignored
    graph = admin_client.get("/item-graph").json
    assert len(graph["nodes"]) == 0

    # Unless it is asked for directly
    graph = admin_client.get(f"/item-graph/{item_id}").json
    assert len(graph["nodes"]) == 1

    # Now make a sample and connect it to the starting material; check that the
    # starting material is now shown by default
    parent = Sample(
        item_id="parent",
        synthesis_constituents=[
            {"item": {"item_id": item_id, "type": "starting_materials"}, "quantity": None}
        ],
    )

    creation = admin_client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(parent.json())},
    )

    assert creation.status_code == 201

    graph = admin_client.get("/item-graph").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
