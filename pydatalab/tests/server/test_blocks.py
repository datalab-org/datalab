import pytest

from pydatalab.apps import BLOCK_TYPES, BLOCKS


@pytest.mark.dependency()
def test_get_all_available_block_types():
    """Test that we can enumerate all available block types."""
    assert len(BLOCKS) > 0
    assert len(BLOCK_TYPES) > 0

    for block_class in BLOCKS:
        assert block_class.blocktype is not None
        assert block_class.name is not None
        assert (
            block_class.description is not None
        ), f"{block_class.blocktype} is missing a description"
        assert block_class.blocktype in BLOCK_TYPES
        assert BLOCK_TYPES[block_class.blocktype] == block_class


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
@pytest.mark.parametrize("block_type", list(BLOCK_TYPES.keys()))
def test_create_sample_with_each_block_type(admin_client, block_type, default_sample_dict):
    """Test creating a sample and adding each available block type via API."""
    sample_id = f"test_sample_with_{block_type.replace('-', '_')}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert (
        response.status_code == 201
    ), f"Failed to create sample for {block_type}: {response.json()}"
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json()}"
    assert response.json["status"] == "success"
    assert response.json["new_block_obj"]
    assert response.json["new_block_obj"]["blocktype"] == block_type
    assert response.json["new_block_insert_index"] == 0

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    item_data = response.json["item_data"]
    assert "blocks_obj" in item_data
    assert len(item_data["blocks_obj"]) == 1
    first_block = next(iter(item_data["blocks_obj"].values()))
    assert first_block["blocktype"] == block_type


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
def test_invalid_block_type(admin_client, default_sample_dict):
    """Test that invalid block types are rejected."""
    sample_id = "test_sample_invalid_block"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": "nonexistent_block_type",
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 400
    assert "Invalid block type" in response.json["message"]


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
def test_add_multiple_blocks_to_sample(admin_client, default_sample_dict):
    """Test adding multiple different block types to the same sample."""
    sample_id = "test_sample_multiple_blocks"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201

    block_types_to_test = list(BLOCK_TYPES.keys())[:3]
    block_ids = []

    for i, block_type in enumerate(block_types_to_test):
        response = admin_client.post(
            "/add-data-block/",
            json={
                "block_type": block_type,
                "item_id": sample_id,
                "index": i,
            },
        )

        assert response.status_code == 200, f"Failed to add {block_type} block at index {i}"
        assert response.json["status"] == "success"
        block_ids.append(response.json["new_block_obj"]["block_id"])

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200

    item_data = response.json["item_data"]
    assert len(item_data["blocks_obj"]) == len(block_types_to_test)
    assert len(item_data["display_order"]) == len(block_types_to_test)

    added_block_types = [block["blocktype"] for block in item_data["blocks_obj"].values()]
    for block_type in block_types_to_test:
        assert block_type in added_block_types


def test_block_permissions(client, admin_client, unauthenticated_client, default_sample_dict):
    """Test that normal users can add blocks to samples they have access to, but unauthenticated users cannot."""
    sample_id = "test_sample_user_permissions"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    # Create sample with normal user
    response = client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201

    block_type = list(BLOCK_TYPES.keys())[0]

    response = client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    second_block_type = list(BLOCK_TYPES.keys())[1] if len(BLOCK_TYPES) > 1 else block_type
    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": second_block_type,
            "item_id": sample_id,
            "index": 1,
        },
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = unauthenticated_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 2,
        },
    )
    assert response.status_code == 401


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
def test_add_block_to_nonexistent_item(admin_client):
    """Test that adding a block to a nonexistent item fails gracefully."""
    block_type = list(BLOCK_TYPES.keys())[0]

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": "nonexistent_item_id",
            "index": 0,
        },
    )

    assert response.status_code == 400
    assert "Update failed" in response.json["message"]


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
def test_block_info_endpoint_contains_all_blocks(client):
    """Test that the /info/blocks endpoint returns all available block types."""
    response = client.get("/info/blocks")
    assert response.status_code == 200

    returned_block_types = {block["id"] for block in response.json["data"]}
    expected_block_types = set(BLOCK_TYPES.keys())

    assert expected_block_types.issubset(
        returned_block_types
    ), f"Missing block types in /info/blocks: {expected_block_types - returned_block_types}"
