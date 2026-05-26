from pathlib import Path

MPR_FILE = (
    Path(__file__).parent.parent.parent
    / "example_data"
    / "echem"
    / "jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
)


def _upload_mpr_and_add_cycle_block(client, item_id):
    """Create a sample, upload the .mpr file, and add a cycle block.

    Returns (block_id, file_id) without processing the block.
    """
    response = client.post("/new-sample/", json={"type": "samples", "item_id": item_id})
    assert response.status_code == 201

    with open(MPR_FILE, "rb") as f:
        response = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": item_id,
                "file": [(f, MPR_FILE.name)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )
    assert response.status_code == 201
    file_id = response.json["file_id"]

    response = client.post(
        "/add-data-block/",
        json={"block_type": "cycle", "item_id": item_id, "index": 0},
    )
    assert response.status_code == 200
    block_id = response.json["new_block_obj"]["block_id"]

    return block_id, file_id


def _process_cycle_block(client, item_id, block_id, file_id):
    """Attach a file to a cycle block and process it via update-block."""
    response = client.post(
        "/update-block/",
        json={
            "block_data": {
                "block_id": block_id,
                "blocktype": "cycle",
                "item_id": item_id,
                "file_id": file_id,
                "file_ids": [file_id],
            },
            "item_id": item_id,
            "block_id": block_id,
            "save_to_db": True,
        },
    )
    assert response.status_code == 200
    return response


def test_cycle_block_update_populates_parquet_url(client):
    """Processing a cycle block via update-block should populate parquet_url and bdf_url."""
    item_id = "test_echem_parquet_url"
    block_id, file_id = _upload_mpr_and_add_cycle_block(client, item_id)
    _process_cycle_block(client, item_id, block_id, file_id)

    response = client.get(f"/get-item-data/{item_id}")
    assert response.status_code == 200
    block = response.json["item_data"]["blocks_obj"][block_id]

    assert block.get("parquet_url") is not None, "parquet_url should be set after processing"
    assert block["parquet_url"].endswith("_cached.bdf.parquet")
    assert block.get("bdf_url") is not None, "bdf_url should be set after processing"
    assert block["bdf_url"].endswith(".bdf.csv")


def test_bdf_cache_endpoint_generates_cache_on_demand(client):
    """GET /items/<id>/blocks/<id>/bdf should generate the parquet cache on demand
    when the block has never been processed, and persist the URLs back to the DB."""
    item_id = "test_echem_bdf_endpoint"
    block_id, file_id = _upload_mpr_and_add_cycle_block(client, item_id)

    # Confirm no cache URLs exist yet (block was never processed)
    response = client.get(f"/get-item-data/{item_id}")
    assert response.status_code == 200
    block = response.json["item_data"]["blocks_obj"][block_id]
    assert block.get("parquet_url") is None
    assert block.get("bdf_url") is None

    # Attach the file to the block so the on-demand generation knows which file to load,
    # then clear the URLs to simulate a pre-feature block that has file_ids but no URLs.
    _process_cycle_block(client, item_id, block_id, file_id)

    from pydatalab.mongo import flask_mongo

    flask_mongo.db.items.update_one(
        {"item_id": item_id},
        {
            "$unset": {
                f"blocks_obj.{block_id}.parquet_url": "",
                f"blocks_obj.{block_id}.bdf_url": "",
            }
        },
    )

    response = client.get(f"/get-item-data/{item_id}")
    block = response.json["item_data"]["blocks_obj"][block_id]
    assert block.get("parquet_url") is None

    # Hit the BDF endpoint — should generate on demand and return the file
    response = client.get(f"/items/{item_id}/blocks/{block_id}/bdf?format=parquet")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json}"
    assert len(response.data) > 0
    response.close()

    # Confirm both URLs were persisted back to the DB
    response = client.get(f"/get-item-data/{item_id}")
    block = response.json["item_data"]["blocks_obj"][block_id]
    assert block.get("parquet_url") is not None, (
        "parquet_url should be persisted after on-demand generation"
    )
    assert block.get("bdf_url") is not None, (
        "bdf_url should be persisted after on-demand generation"
    )

    # Also verify the CSV format works
    response = client.get(f"/items/{item_id}/blocks/{block_id}/bdf?format=csv")
    assert response.status_code == 200
    assert len(response.data) > 0
    response.close()
