import pytest


@pytest.mark.dependency()
def test_mentioned_relationship_from_description(client, default_sample_dict):
    """Test that cross-references in description create mentioned relationships."""

    sample_1_dict = default_sample_dict.copy()
    sample_1_dict["item_id"] = "mentioned_sample_1"
    sample_1_dict["name"] = "First Sample"

    sample_2_dict = default_sample_dict.copy()
    sample_2_dict["item_id"] = "mentioned_sample_2"
    sample_2_dict["name"] = "Second Sample"

    response = client.post("/new-sample/", json=sample_1_dict)
    assert response.status_code == 201

    response = client.post("/new-sample/", json=sample_2_dict)
    assert response.status_code == 201

    response = client.get("/get-item-data/mentioned_sample_1")
    assert response.status_code == 200
    item_data = response.json["item_data"]

    item_data["description"] = (
        "<p>This sample is related to "
        '<span data-item-id="mentioned_sample_2" data-item-type="samples" '
        'data-name="Second Sample" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    response = client.get("/get-item-data/mentioned_sample_1")
    assert response.status_code == 200
    relationships = response.json["item_data"].get("relationships", [])

    mentioned_rels = [r for r in relationships if r.get("relation") == "mentioned"]
    assert len(mentioned_rels) == 1
    assert mentioned_rels[0]["item_id"] == "mentioned_sample_2"
    assert mentioned_rels[0]["type"] == "samples"


@pytest.mark.dependency(depends=["test_mentioned_relationship_from_description"])
def test_mentioned_relationship_from_block_comment(client, default_sample_dict):
    """Test that cross-references in block comments create mentioned relationships."""

    sample_3_dict = default_sample_dict.copy()
    sample_3_dict["item_id"] = "mentioned_sample_3"
    sample_3_dict["name"] = "Third Sample"

    response = client.post("/new-sample/", json=sample_3_dict)
    assert response.status_code == 201

    response = client.get("/get-item-data/mentioned_sample_1")
    item_data = response.json["item_data"]

    item_data["description"] = "<p>Clean description</p>"

    block_id = "test_block_1"
    item_data["blocks_obj"] = {
        block_id: {
            "blocktype": "comment",
            "block_id": block_id,
            "freeform_comment": (
                "<p>Check this sample: "
                '<span data-item-id="mentioned_sample_3" data-item-type="samples" '
                'data-name="Third Sample" data-chemform="" data-type="crossreference"></span>'
                "</p>"
            ),
        }
    }

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    response = client.get("/get-item-data/mentioned_sample_1")
    relationships = response.json["item_data"].get("relationships", [])

    mentioned_rels = [r for r in relationships if r.get("relation") == "mentioned"]
    assert len(mentioned_rels) == 1
    assert mentioned_rels[0]["item_id"] == "mentioned_sample_3"


@pytest.mark.dependency(depends=["test_mentioned_relationship_from_block_comment"])
def test_multiple_mentioned_relationships(client, default_sample_dict):
    """Test multiple cross-references create multiple mentioned relationships."""

    response = client.get("/get-item-data/mentioned_sample_1")
    item_data = response.json["item_data"]

    item_data["description"] = (
        "<p>Related to "
        '<span data-item-id="mentioned_sample_2" data-item-type="samples" '
        'data-name="Second Sample" data-chemform="" data-type="crossreference"></span> and '
        '<span data-item-id="mentioned_sample_3" data-item-type="samples" '
        'data-name="Third Sample" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    item_data["blocks_obj"] = {}

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    response = client.get("/get-item-data/mentioned_sample_1")
    relationships = response.json["item_data"].get("relationships", [])

    mentioned_rels = [r for r in relationships if r.get("relation") == "mentioned"]
    assert len(mentioned_rels) == 2
    mentioned_ids = {r["item_id"] for r in mentioned_rels}
    assert mentioned_ids == {"mentioned_sample_2", "mentioned_sample_3"}


@pytest.mark.dependency(depends=["test_multiple_mentioned_relationships"])
def test_remove_mentioned_relationships(client):
    """Test that removing cross-references removes mentioned relationships."""

    response = client.get("/get-item-data/mentioned_sample_1")
    item_data = response.json["item_data"]

    item_data["description"] = "<p>No more cross-references</p>"
    item_data["blocks_obj"] = {}

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    response = client.get("/get-item-data/mentioned_sample_1")
    relationships = response.json["item_data"].get("relationships", [])

    mentioned_rels = [r for r in relationships if r.get("relation") == "mentioned"]
    assert len(mentioned_rels) == 0


@pytest.mark.dependency(depends=["test_remove_mentioned_relationships"])
def test_mentioned_relationship_no_self_reference(client, default_sample_dict):
    """Test that self-referencing cross-references don't create relationships."""

    response = client.get("/get-item-data/mentioned_sample_1")
    item_data = response.json["item_data"]

    item_data["description"] = (
        "<p>Reference to myself: "
        '<span data-item-id="mentioned_sample_1" data-item-type="samples" '
        'data-name="First Sample" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    response = client.get("/get-item-data/mentioned_sample_1")
    relationships = response.json["item_data"].get("relationships", [])

    mentioned_rels = [r for r in relationships if r.get("relation") == "mentioned"]
    assert len(mentioned_rels) == 0


@pytest.mark.dependency(depends=["test_mentioned_relationship_no_self_reference"])
def test_mentioned_relationships_in_graph(client):
    """Test that mentioned relationships appear in item graph."""

    response = client.get("/get-item-data/mentioned_sample_1")
    item_data = response.json["item_data"]

    item_data["description"] = (
        "<p>Related to "
        '<span data-item-id="mentioned_sample_2" data-item-type="samples" '
        'data-name="Second Sample" data-chemform="" data-type="crossreference"></span>'
        "</p>"
    )

    response = client.post("/save-item/", json={"item_id": "mentioned_sample_1", "data": item_data})
    assert response.status_code == 200

    graph = client.get("/item-graph/mentioned_sample_1").json
    assert graph["status"] == "success"

    node_ids = {node["data"]["id"] for node in graph["nodes"]}
    assert "mentioned_sample_2" in node_ids

    edges = graph["edges"]
    mentioned_edges = [e for e in edges if e["data"].get("relation_type") == "mentioned"]
    assert len(mentioned_edges) == 1
    assert mentioned_edges[0]["data"]["source"] == "mentioned_sample_1"
    assert mentioned_edges[0]["data"]["target"] == "mentioned_sample_2"
