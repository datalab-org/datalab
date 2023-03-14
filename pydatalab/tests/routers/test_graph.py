import json

from pydatalab.models import Sample
from pydatalab.models.relationships import RelationshipType, TypedRelationship


def test_new_sample_with_relationships(client):

    parent = Sample(
        item_id="parent",
        relationships=[
            TypedRelationship(type="samples", relation=RelationshipType.PARENT, item_id="child_1"),
            TypedRelationship(type="samples", relation=RelationshipType.PARENT, item_id="child_2"),
            TypedRelationship(
                type="samples", relation=RelationshipType.PARENT, item_id="missing_child"
            ),
        ],
    ).json()

    child_1 = Sample(
        item_id="child_1",
        relationships=[
            TypedRelationship(type="samples", relation=RelationshipType.CHILD, item_id="parent"),
        ],
    ).json()

    child_2 = Sample(
        item_id="child_2",
        relationships=[
            TypedRelationship(type="samples", relation=RelationshipType.CHILD, item_id="parent"),
        ],
    ).json()

    missing_child = Sample(
        item_id="missing_child",
        relationships=[
            TypedRelationship(type="samples", relation=RelationshipType.CHILD, item_id="parent"),
        ],
    ).json()

    new_samples = [json.loads(d) for d in [parent, child_1, child_2, missing_child]]

    response = client.post(
        "/new-samples/",
        json={"new_sample_datas": new_samples},
    )

    assert response.status_code == 207
    assert response.json["http_codes"] == [201, 201, 201, 201]

    graph = client.get("/item-graph/").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
        "missing_child",
    }
    assert len(graph["edges"]) == 3

    response = client.post("/delete-sample/", json={"item_id": "missing_child"})
    assert response

    graph = client.get("/item-graph/").json
    assert {n["data"]["id"] for n in graph["nodes"]} == {
        "parent",
        "child_1",
        "child_2",
    }

    assert len(graph["edges"]) == 2
