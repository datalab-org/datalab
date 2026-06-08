"""Tests for the cross-sample block comparison endpoint (``/blocks/compare/``)."""

from uuid import uuid4

import pytest

XRD_FILE = "XRD/Scan_C4.xrdml"


def _make_sample_with_xrd_block(admin_client, default_sample_dict, example_data_dir, sample_id):
    """Create a sample with a single, file-backed XRD block and return
    ``(sample_id, block_id)``."""
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, response.json

    response = admin_client.post(
        "/add-data-block/",
        json={"block_type": "xrd", "item_id": sample_id, "index": 0},
    )
    assert response.status_code == 200, response.json
    block_id = response.json["new_block_obj"]["block_id"]

    example_file = example_data_dir / XRD_FILE
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
    assert response.status_code == 201, response.json
    file_id = response.json["file_id"]

    response = admin_client.get(f"/get-item-data/{sample_id}")
    block_data = response.json["item_data"]["blocks_obj"][block_id]
    block_data["file_id"] = file_id
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200, response.json
    assert response.json["new_block_data"].get("errors") is None

    return sample_id, block_id


@pytest.fixture()
def two_xrd_samples(admin_client, default_sample_dict, example_data_dir):
    suffix = uuid4().hex[:8]
    a = _make_sample_with_xrd_block(
        admin_client, default_sample_dict, example_data_dir, f"compare_xrd_a_{suffix}"
    )
    b = _make_sample_with_xrd_block(
        admin_client, default_sample_dict, example_data_dir, f"compare_xrd_b_{suffix}"
    )
    return a, b


def test_compare_two_xrd_blocks(admin_client, two_xrd_samples):
    (item_a, block_a), (item_b, block_b) = two_xrd_samples

    response = admin_client.post(
        "/blocks/compare/",
        json={
            "blocks": [
                {"item_id": item_a, "block_id": block_a, "label": "A"},
                {"item_id": item_b, "block_id": block_b, "label": "B"},
            ]
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["status"] == "success"
    assert response.json["bokeh_plot_data"] is not None


def test_compare_block_without_explicit_file_id(
    admin_client, default_sample_dict, example_data_dir, two_xrd_samples
):
    """An XRD block with no explicit ``file_id`` auto-plots all compatible attached
    files; the overlay must resolve those files rather than erroring."""
    (item_a, block_a), _ = two_xrd_samples

    # Build a sample whose XRD block has a compatible file attached but no file_id set.
    sample_id = f"compare_xrd_nofileid_{uuid4().hex[:8]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id
    assert admin_client.post("/new-sample/", json=sample_data).status_code == 201

    response = admin_client.post(
        "/add-data-block/",
        json={"block_type": "xrd", "item_id": sample_id, "index": 0},
    )
    block_id = response.json["new_block_obj"]["block_id"]

    example_file = example_data_dir / XRD_FILE
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
    assert response.status_code == 201
    # Note: deliberately do NOT set file_id on the block.

    response = admin_client.post(
        "/blocks/compare/",
        json={
            "blocks": [
                {"item_id": item_a, "block_id": block_a},
                {"item_id": sample_id, "block_id": block_id},
            ]
        },
    )
    assert response.status_code == 200, response.json
    assert response.json["bokeh_plot_data"] is not None


def test_compare_requires_two_blocks(admin_client, two_xrd_samples):
    (item_a, block_a), _ = two_xrd_samples

    response = admin_client.post(
        "/blocks/compare/",
        json={"blocks": [{"item_id": item_a, "block_id": block_a}]},
    )
    assert response.status_code == 400


def test_compare_missing_block(admin_client, two_xrd_samples):
    (item_a, block_a), _ = two_xrd_samples

    response = admin_client.post(
        "/blocks/compare/",
        json={
            "blocks": [
                {"item_id": item_a, "block_id": block_a},
                {"item_id": item_a, "block_id": "nonexistent"},
            ]
        },
    )
    assert response.status_code == 400


def test_compare_unsupported_block_type(admin_client, default_sample_dict):
    """A block type that does not implement get_comparison_data should be rejected."""
    sample_id = f"compare_comment_sample_{uuid4().hex[:8]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id
    assert admin_client.post("/new-sample/", json=sample_data).status_code == 201

    block_ids = []
    for index in range(2):
        response = admin_client.post(
            "/add-data-block/",
            json={"block_type": "comment", "item_id": sample_id, "index": index},
        )
        assert response.status_code == 200
        block_ids.append(response.json["new_block_obj"]["block_id"])

    response = admin_client.post(
        "/blocks/compare/",
        json={
            "blocks": [
                {"item_id": sample_id, "block_id": block_ids[0]},
                {"item_id": sample_id, "block_id": block_ids[1]},
            ]
        },
    )
    assert response.status_code == 400
    assert "not supported" in response.json["message"]


def test_supports_overlay_flag(client):
    """The /info/blocks endpoint should advertise which block types support overlay."""
    response = client.get("/info/blocks")
    assert response.status_code == 200
    supports = {d["id"]: d["attributes"].get("supports_overlay") for d in response.json["data"]}

    # XRD implements get_comparison_data; comment does not.
    assert supports.get("xrd") is True
    assert supports.get("comment") is False


def test_compare_requires_auth(unauthenticated_client, two_xrd_samples):
    (item_a, block_a), (item_b, block_b) = two_xrd_samples

    response = unauthenticated_client.post(
        "/blocks/compare/",
        json={
            "blocks": [
                {"item_id": item_a, "block_id": block_a},
                {"item_id": item_b, "block_id": block_b},
            ]
        },
    )
    assert response.status_code == 401
