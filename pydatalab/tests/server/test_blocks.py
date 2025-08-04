from pathlib import Path

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
        assert block_class.description is not None, (
            f"{block_class.blocktype} is missing a description"
        )
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
    assert response.status_code == 201, (
        f"Failed to create sample for {block_type}: {response.json()}"
    )
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

    assert expected_block_types.issubset(returned_block_types), (
        f"Missing block types in /info/blocks: {expected_block_types - returned_block_types}"
    )


@pytest.mark.dependency(depends=["test_get_all_available_block_types"])
def test_create_sample_with_example_files(admin_client, default_sample_dict):
    """Create a  test sample with multiple block types and attached example files."""

    sample_id = "test_sample_with_files"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    block_file_mapping = {
        "tabular": "csv",
        "cycle": "echem",
        "ftir": "FTIR",
        "nmr": "NMR",
        "raman": "raman",
        "ms": "TGA-MS",
        "uv-vis": "UV-Vis",
        "xrd": "XRD",
        "media": "media",
    }

    preferred_files = {
        "cycle": "jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr",
        "tabular": "simple.csv",
        "ftir": "2024-10-10_FeSO4_ref.asp",
        "nmr": "1.zip",
        "raman": "raman_example.txt",
        "ms": "20221128 134958 TGA MS Megan.asc",
        "xrd": "Scan_C4.xrdml",
        "media": "grey_group_logo.jpeg",
    }

    example_data_path = Path(__file__).parent.parent.parent / "example_data"
    added_blocks = {}
    uploaded_files = []
    block_index = 0

    for block_type, folder_name in block_file_mapping.items():
        response = admin_client.post(
            "/add-data-block/",
            json={
                "block_type": block_type,
                "item_id": sample_id,
                "index": block_index,
            },
        )

        assert response.status_code == 200, f"Failed to add {block_type} block: {response.json()}"
        assert response.json["status"] == "success"

        block_data = response.json["new_block_obj"]
        block_id = block_data["block_id"]
        added_blocks[block_type] = {"block_id": block_id, "index": block_index}

        if block_type == "uv-vis":
            folder_path = example_data_path / folder_name
            if folder_path.exists():
                uv_files = list(folder_path.glob("*"))
                assert len(uv_files) >= 2, f"UV-Vis needs at least 2 files, found {len(uv_files)}"

                file_ids = []
                for i, uv_file in enumerate(uv_files[:2]):
                    with open(uv_file, "rb") as f:
                        response = admin_client.post(
                            "/upload-file/",
                            buffered=True,
                            content_type="multipart/form-data",
                            data={
                                "item_id": sample_id,
                                "file": [(f, uv_file.name)],
                                "type": "application/octet-stream",
                                "replace_file": "null",
                                "relativePath": "null",
                            },
                        )

                    if response.status_code == 201:
                        assert response.json["status"] == "success"
                        file_id = response.json["file_id"]
                        file_ids.append(file_id)
                        uploaded_files.append({"block_type": block_type, "filename": uv_file.name})

                if file_ids:
                    response = admin_client.get(f"/get-item-data/{sample_id}")
                    assert response.status_code == 200
                    item_data = response.json["item_data"]
                    block_data = item_data["blocks_obj"][block_id]
                    block_data["file_id"] = file_ids[0]
                    block_data["selected_file_order"] = file_ids

                    response = admin_client.post(
                        "/update-block/", json={"block_data": block_data, "save_to_db": True}
                    )

                    assert response.status_code == 200

        else:
            folder_path = example_data_path / folder_name
            if folder_path.exists():
                files_in_folder = list(folder_path.glob("*"))
                assert len(files_in_folder) > 0, f"No files found in {folder_path}"

                if block_type in preferred_files:
                    preferred_file = folder_path / preferred_files[block_type]
                    if preferred_file.exists():
                        example_file = preferred_file
                    else:
                        example_file = files_in_folder[0]
                else:
                    example_file = files_in_folder[0]

                with open(example_file, "rb") as f:
                    response = admin_client.post(
                        "/upload-file/",
                        buffered=True,
                        content_type="multipart/form-data",
                        data={
                            "item_id": sample_id,
                            "file": [(f, example_file.name)],
                            "type": "application/octet-stream",
                            "replace_file": "null",
                            "relativePath": "null",
                        },
                    )

                assert response.status_code == 201, f"Failed to upload {example_file.name}"
                assert response.json["status"] == "success"
                file_id = response.json["file_id"]

                response = admin_client.get(f"/get-item-data/{sample_id}")
                assert response.status_code == 200
                item_data = response.json["item_data"]
                block_data = item_data["blocks_obj"][block_id]
                block_data["file_id"] = file_id

                response = admin_client.post(
                    "/update-block/", json={"block_data": block_data, "save_to_db": True}
                )
                assert response.status_code == 200
                uploaded_files.append({"block_type": block_type, "filename": example_file.name})

        block_index += 1

    response = admin_client.get(f"/get-item-data/{sample_id}?load_blocks=1")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    item_data = response.json["item_data"]
    assert "blocks_obj" in item_data
    assert len(item_data["blocks_obj"]) == len(added_blocks)
    assert len(item_data["display_order"]) == len(added_blocks)

    assert "file_ObjectIds" in item_data
    assert len(item_data["file_ObjectIds"]) >= len(uploaded_files)

    block_types_in_sample = [block["blocktype"] for block in item_data["blocks_obj"].values()]
    expected_block_types = list(block_file_mapping.keys())

    for expected_type in expected_block_types:
        assert expected_type in block_types_in_sample

    if block_type != "media":
        assert response.json["new_block_data"]["bokeh_plot_data"] is not None

    blocks_with_files = sum(1 for block in item_data["blocks_obj"].values() if block.get("file_id"))
    blocks_without_files = [
        block["blocktype"] for block in item_data["blocks_obj"].values() if not block.get("file_id")
    ]

    assert blocks_with_files >= len(uploaded_files) // 2, (
        f"Not enough blocks have files attached. Blocks without files: {blocks_without_files}"
    )
