"""More item graph tests (in addition to `test_graph.py`) that
are written to be more isolated from one another.

"""

import json

from pydatalab.models import Sample, StartingMaterial


def test_single_starting_material(admin_client, client):
    item_id = "material"

    material = StartingMaterial(item_id=item_id)

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(material.json())},
    )

    assert creation.status_code == 201

    material_refcode = creation.json["sample_list_entry"]["refcode"]

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
            {
                "item": {
                    "item_id": item_id,
                    "refcode": material_refcode,
                    "type": "starting_materials",
                },
                "quantity": None,
            }
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(parent.json())},
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

    parent_response = client.get("/get-item-data/parent")
    parent_refcode = parent_response.json["item_data"]["refcode"]

    # Now add a few more samples in a chain and check that only the relevant ones are shown
    child = Sample(
        item_id="child",
        synthesis_constituents=[
            {
                "item": {
                    "item_id": "parent",
                    "refcode": parent_refcode,
                    "type": "samples",
                },
                "quantity": None,
            }
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(child.json())},
    )

    assert creation.status_code == 201

    child_response = client.get("/get-item-data/child")
    child_refcode = child_response.json["item_data"]["refcode"]

    grandchild = Sample(
        item_id="grandchild",
        synthesis_constituents=[
            {
                "item": {
                    "item_id": "child",
                    "refcode": child_refcode,
                    "type": "samples",
                },
                "quantity": None,
            }
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(grandchild.json())},
    )

    assert creation.status_code == 201

    grandchild_response = client.get("/get-item-data/grandchild")
    grandchild_refcode = grandchild_response.json["item_data"]["refcode"]

    great_grandchild = Sample(
        item_id="great-grandchild",
        synthesis_constituents=[
            {
                "item": {
                    "item_id": "grandchild",
                    "refcode": grandchild_refcode,
                    "type": "samples",
                },
                "quantity": None,
            }
        ],
    )

    creation = client.post(
        "/new-sample/",
        json={"new_sample_data": json.loads(great_grandchild.json())},
    )

    assert creation.status_code == 201

    graph = client.get("/item-graph").json
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4

    # Check for bug where this behaviour was inconsistent between admin and non-admin users
    graph = admin_client.get("/item-graph/great-grandchild").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    great_grandchild_response = admin_client.get("/get-item-data/great-grandchild")
    great_grandchild_refcode = great_grandchild_response.json["item_data"]["refcode"]

    # Add an admin only item and check that the non-admin user still sees the same graph
    admin_great_great_grandchild = Sample(
        item_id="admin-great-great-grandchild",
        synthesis_constituents=[
            {
                "item": {
                    "item_id": "great-grandchild",
                    "refcode": great_grandchild_refcode,
                    "type": "samples",
                },
                "quantity": None,
            }
        ],
    )

    creation = admin_client.post(
        "/new-sample/", json={"new_sample_data": json.loads(admin_great_great_grandchild.json())}
    )

    graph = admin_client.get("/item-graph/great-grandchild").json
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

    collection_graph = admin_client.get("/item-graph?collection_id=test-collection").json
    assert len(collection_graph["nodes"]) == 1
    assert len(collection_graph["edges"]) == 0

    graph = client.get("/item-graph/great-grandchild?hide_collections=false").json
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    admin_graph = admin_client.get("/item-graph/great-grandchild?hide_collections=false").json
    assert len(admin_graph["nodes"]) == 4
    assert len(admin_graph["edges"]) == 3
