from pathlib import Path

import pytest

from pydatalab.apps import BLOCK_TYPES, BLOCKS


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


@pytest.mark.parametrize("block_type", list(BLOCK_TYPES.keys()))
def test_create_sample_with_each_block_type(admin_client, block_type, default_sample_dict):
    """Test creating a sample and adding each available block type via API."""
    sample_id = f"test_sample_with_{block_type.replace('-', '_')}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, f"Failed to create sample for {block_type}: {response.json}"
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
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

    assert response.status_code == 501
    assert "Invalid block type" in response.json["message"]


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


def test_block_info_endpoint_contains_all_blocks(client):
    """Test that the /info/blocks endpoint returns all available block types."""
    response = client.get("/info/blocks")
    assert response.status_code == 200

    returned_block_types = {block["id"] for block in response.json["data"]}
    expected_block_types = set(BLOCK_TYPES.keys())

    assert expected_block_types.issubset(returned_block_types), (
        f"Missing block types in /info/blocks: {expected_block_types - returned_block_types}"
    )


def test_uvvis_block_lifecycle(admin_client, default_sample_dict, example_data_dir):
    block_type = "uv-vis"

    sample_id = f"test_sample_with_files-{block_type}-lifecycle"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
    assert response.json["status"] == "success"

    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]

    uvvis_folder = example_data_dir / "UV-Vis"

    example_files = uvvis_folder.glob("*")
    example_file_ids = []

    for example_file in example_files:
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
            example_file_ids.append(file_id)

    assert len(example_file_ids) == 3

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    item_data = response.json["item_data"]
    block_data = item_data["blocks_obj"][block_id]
    block_data["file_id"] = example_file_ids[0]
    block_data["selected_file_order"] = example_file_ids

    response = admin_client.post("/update-block/", json={"block_data": block_data})

    assert response.status_code == 200
    web_block = response.json["new_block_data"]
    assert web_block["file_id"] == example_file_ids[0]
    assert "bokeh_plot_data" in web_block
    assert web_block.get("errors") is None


def test_echem_block_lifecycle(admin_client, default_sample_dict, example_data_dir):
    block_type = "cycle"

    sample_id = f"test_sample_with_files-{block_type}-lifecycle"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
    assert response.json["status"] == "success"

    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]

    # Upload multiple echem files
    echem_folder = example_data_dir / "echem"
    example_files = list(echem_folder.glob("*.mpr"))[:2]
    example_file_ids = []

    for example_file in example_files:
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
            file_ids = response.json["file_id"]
            example_file_ids.append(file_ids)

    assert len(example_file_ids) == 2

    # Update block with multiple file_ids
    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    item_data = response.json["item_data"]
    block_data = item_data["blocks_obj"][block_id]
    block_data["mode"] = "multi"
    block_data["file_ids"] = example_file_ids

    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    web_block = response.json["new_block_data"]

    assert "bokeh_plot_data" in web_block
    assert web_block["bokeh_plot_data"] is not None
    assert web_block.get("errors") is None

    # Update block with comparison files (use single mode + comparison_file_ids)
    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    item_data = response.json["item_data"]
    block_data = item_data["blocks_obj"][block_id]
    block_data["mode"] = "single"
    block_data["file_ids"] = [example_file_ids[0]]
    block_data["comparison_file_ids"] = [example_file_ids[1]]

    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    web_block = response.json["new_block_data"]

    assert "bokeh_plot_data" in web_block
    assert web_block["bokeh_plot_data"] is not None
    assert web_block.get("errors") is None

    # Test for only one file_id
    block_data["mode"] = "single"
    block_data["file_ids"] = [example_file_ids[0]]

    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    web_block = response.json["new_block_data"]
    assert "bokeh_plot_data" in web_block
    assert web_block["bokeh_plot_data"] is not None
    assert web_block.get("errors") is None


def test_xrd_block_lifecycle(admin_client, client, user_id, default_sample_dict, example_data_dir):
    from pydatalab.apps.xrd import XRDBlock

    block_type = "xrd"

    sample_id = f"test_sample_with_files-{block_type}-lifecycle"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    refcode = response.json["sample_list_entry"]["refcode"]

    response = admin_client.patch(
        f"/items/{refcode}/permissions", json={"creators": [{"immutable_id": str(user_id)}]}
    )

    assert response.status_code == 200

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
    assert response.json["status"] == "success"

    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]

    block_file = "XRD/cod_9004112.cif"

    example_file = example_data_dir / block_file

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
    block_data["wavelength"] = 2.0

    response = admin_client.post("/update-block/", json={"block_data": block_data})

    web_block = response.json["new_block_data"]
    assert "bokeh_plot_data" in web_block
    assert "computed" in web_block
    assert web_block["wavelength"] == 2.0
    assert "peak_data" in web_block["computed"]
    assert "file_id" in web_block
    assert web_block["file_id"] == file_id
    assert web_block.get("errors") is None

    # Check a non-admin creator can also see the block
    response = client.post("/update-block/", json={"block_data": block_data})

    assert "new_block_data" in response.json
    web_block = response.json["new_block_data"]
    assert "bokeh_plot_data" in web_block
    assert "computed" in web_block
    assert web_block["wavelength"] == 2.0
    assert "peak_data" in web_block["computed"]
    assert "file_id" in web_block
    assert web_block["file_id"] == file_id
    assert web_block.get("errors") is None

    block = XRDBlock.from_web(web_block)
    db = block.to_db()
    # 'computed' keys should be dropped when loading from web
    assert "bokeh_plot_data" not in db
    assert "computed" not in db
    assert db["wavelength"] == 2.0

    # But they should still be in the database
    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200

    item_data = response.json["item_data"]
    assert response.json["status"] == "success"
    assert "blocks_obj" in item_data
    block = item_data["blocks_obj"][block_id]
    assert "computed" in block
    assert "peak_data" in block["computed"]
    assert block["wavelength"] == 2.0


def test_comment_block_manipulation(admin_client, default_sample_dict, database):
    """Create a test sample with a comment block and test it for
    dealing with unhandled data."""

    block_type = "comment"

    sample_id = "test_sample_with_files-comment"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
    assert response.json["status"] == "success"

    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]
    block_data["freeform_comment"] = "This is a test comment block."
    block_data["title"] = "Test Comment Block"
    block_data["errors"] = ["Test Network Failure"]

    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["new_block_data"]["blocktype"] == block_type
    assert response.json["new_block_data"]["freeform_comment"] == "This is a test comment block."
    assert response.json["new_block_data"]["title"] == "Test Comment Block"
    assert response.json["new_block_data"].get("errors") is None

    # Check that this result was actually stored
    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    item_data = response.json["item_data"]
    assert response.json["status"] == "success"
    assert (
        response.json["item_data"]["blocks_obj"][block_id]["freeform_comment"]
        == "This is a test comment block."
    )
    assert "errors" not in response.json["item_data"]["blocks_obj"][block_id]

    # Try to add some bad data
    block_data["bokeh_plot_data"] = {"bokeh": "json"}
    block_data["random_new_key"] = "test new key"
    block_data["freeform_comment"] = "This is a test comment block with extra data."
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["new_block_data"]["blocktype"] == block_type
    assert (
        response.json["new_block_data"]["freeform_comment"]
        == "This is a test comment block with extra data."
    )
    assert response.json["new_block_data"]["title"] == "Test Comment Block"
    assert "bokeh_plot_data" not in response.json["new_block_data"]

    # Extra random keys will be in the response (in case they are parameters for the block that are not yet handled,
    # but they will not be stored in the database)
    assert "random_new_key" in response.json["new_block_data"]

    raw_item = database.items.find_one({"item_id": sample_id})
    assert raw_item
    raw_block = raw_item["blocks_obj"][block_id]
    assert "bokeh_plot_data" not in raw_block
    # assert "random_new_key" not in raw_block
    assert "errors" not in raw_block

    # Finally, try to update using the save-item endpoint, and make sure any bad data gets stripped out
    item_data["blocks_obj"][block_id]["bokeh_plot_data"] = {"bokeh": "json"}
    item_data["blocks_obj"][block_id]["random_new_key"] = "test new key again"
    item_data["blocks_obj"][block_id]["freeform_comment"] = "This is the latest test comment."

    admin_client.post("/save-item/", json={"item_id": sample_id, "data": item_data})
    assert response.status_code == 200

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    item_data = response.json["item_data"]
    block = item_data["blocks_obj"][block_id]

    assert block["freeform_comment"] == "This is the latest test comment."
    assert block.get("bokeh_plot_data") is None
    assert block["random_new_key"] == "test new key again"


@pytest.mark.parametrize(
    "block_type, block_file",
    [
        ("tabular", "csv/simple.csv"),
        ("cycle", "echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"),
        ("ftir", "FTIR/2024-10-10_FeSO4_ref.asp"),
        ("nmr", "NMR/1.zip"),
        ("raman", "raman/raman_example.txt"),
        ("ms", "TGA-MS/20221128 134958 TGA MS Megan.asc"),
        ("xrd", "XRD/Scan_C4.xrdml"),
        ("media", "media/grey_group_logo.tif"),
    ],
)
def test_create_sample_with_example_files(
    block_type, block_file, admin_client, example_data_dir, default_sample_dict, database
):
    """Create a test sample with a block with file uploaded and test for errors."""

    sample_id = f"test_sample_with_files-{block_type}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201
    assert response.json["status"] == "success"

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    assert response.status_code == 200, f"Failed to add {block_type} block: {response.json}"
    assert response.json["status"] == "success"

    block_data = response.json["new_block_obj"]
    block_id = block_data["block_id"]

    example_file = example_data_dir / block_file

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

    # For cycle blocks, need to set mode and file_ids rather than file_id
    if block_type == "cycle":
        block_data["mode"] = "single"
        block_data["file_ids"] = [file_id]

    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["new_block_data"]["blocktype"] == block_type

    # Some specific checks for different block types:
    if block_type != "media":
        assert response.json["new_block_data"]["bokeh_plot_data"] is not None

    if block_type == "xrd":
        assert response.json["new_block_data"]["computed"]["peak_data"] is not None

    # For the media block, check that a TIF image is present and can be saved correctly
    if block_type == "media":
        block_data = response.json["new_block_data"]
        assert "b64_encoded_image" in block_data

        response = admin_client.get(f"/get-item-data/{sample_id}")
        assert response.status_code == 200
        item_data = response.json["item_data"]

        item_data["blocks_obj"][block_id] = block_data
        response = admin_client.post("/save-item/", json={"item_id": sample_id, "data": item_data})
        assert response.status_code == 200

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    assert response.json["status"] == "success"

    item_data = response.json["item_data"]
    assert "blocks_obj" in item_data

    if block_type == "xrd":
        doc = database.items.find_one({"item_id": sample_id}, projection={"blocks_obj": 1})
        assert doc["blocks_obj"][block_id]["computed"]["peak_data"] is not None


@pytest.fixture()
def create_large_xye_file(tmpdir):
    """Create a relatively large .xye file for testing tabular block serialization and memory usage,
    as a separate fixture to avoid it being counted in memray profile."""

    fname = Path(tmpdir / "large_table.xye")

    # Make a dataframe of ~3 columns and 1,000,000 rows
    # totalling ~2.4 MB (raw floats), so maybe 3 MB as a dataframe
    import numpy as np
    import pandas as pd

    N = 50_000

    pd.DataFrame(
        {
            "two_theta": np.array(np.linspace(5, 85, N), dtype=np.float64),
            "intensity": np.array(np.random.rand(N), dtype=np.float64),
            "error": np.array(0.1 * np.random.rand(N), dtype=np.float64),
        }
    ).to_csv(fname, sep=",", index=False)

    yield fname


@pytest.mark.limit_memory("110MB")
def test_large_fake_xrd_data_block_serialization(
    admin_client, default_sample_dict, tmpdir, create_large_xye_file
):
    """Make a fake xye file with relatively large data and test serialization
    memory usage in particular.

    As of the time of writing, we get a breakdown like:

        > Allocation results for tests/server/test_blocks.py::test_large_fake_xrd_data_block_serialization at the high watermark
        >
        > 📦 Total memory allocated: 128.4MiB
        > 📏 Total allocations: 382
        > 📊 Histogram of allocation sizes: |▁▃█  |
        > 🥇 Biggest allocating functions:
        >	- lstsq:./pydatalab/.venv/lib/python3.11/site-packages/numpy/linalg/linalg.py:2326 -> 32.0MiB
        >	- raw_decode:/home/mevans/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/json/decoder.py:353 -> 20.3MiB
        >	- raw_decode:/home/mevans/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/json/decoder.py:353 -> 19.3MiB
        >	- encode:/home/mevans/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/json/encoder.py:203 -> 14.0MiB
        >	- _iterencode_list:/home/mevans/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/json/encoder.py:303 -> 14.0MiB

    """
    import gc

    gc.collect()
    gc.collect()

    block_type = "xrd"

    sample_id = "test_sample_with_large_table"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, f"Failed to create sample for {block_type}: {response.json}"
    assert response.json["status"] == "success"

    with open(create_large_xye_file, "rb") as f:
        response = admin_client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": sample_id,
                "file": [(f, create_large_xye_file.name)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )
        assert response.status_code == 201, f"Failed to upload {create_large_xye_file}"
        assert response.json["status"] == "success"
        file_id = response.json["file_id"]

    response = admin_client.post(
        "/add-data-block/",
        json={
            "block_type": block_type,
            "item_id": sample_id,
            "index": 0,
        },
    )

    block_id = response.json["new_block_obj"]["block_id"]

    gc.collect()

    response = admin_client.post(
        "/update-block/",
        json={
            "block_data": {
                "blocktype": "tabular",
                "item_id": sample_id,
                "file_id": file_id,
                "block_id": block_id,
            },
        },
    )

    assert response.status_code == 200, f"Failed to update tabular block: {response.json}"
    assert response.json["new_block_data"]["bokeh_plot_data"]

    gc.collect()
