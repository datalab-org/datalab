import json
import zipfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from bson import ObjectId

from pydatalab.export import create_eln_file, generate_ro_crate_metadata


def test_generate_ro_crate_metadata():
    """Test RO-Crate metadata generation."""
    collection_data = {
        "_id": ObjectId(),
        "collection_id": "test_collection",
        "title": "Test Collection",
        "description": "A test collection for export",
    }

    child_items = [
        {
            "item_id": "sample1",
            "name": "Sample 1",
            "date": datetime.now(tz=timezone.utc),
            "file_ObjectIds": ["507f1f77bcf86cd799439011"],
        },
        {
            "item_id": "sample2",
            "name": "Sample 2",
        },
    ]

    with patch("pydatalab.export.flask_mongo.db.files.find_one") as mock_find:
        mock_find.return_value = {"name": "test_file.txt"}

        metadata = generate_ro_crate_metadata(collection_data, child_items)

    assert metadata["@context"] == "https://w3id.org/ro/crate/1.1/context"
    assert isinstance(metadata["@graph"], list)

    root = next(item for item in metadata["@graph"] if item["@id"] == "./")
    assert root["@type"] == "Dataset"
    assert root["name"] == "Test Collection"
    assert root["description"] == "A test collection for export"
    assert len(root["hasPart"]) == 2

    sample1 = next(item for item in metadata["@graph"] if item["@id"] == "./sample1/")
    assert sample1["@type"] == "Dataset"
    assert sample1["name"] == "Sample 1"
    assert sample1["identifier"] == "sample1"


def test_create_eln_file_items(database, tmp_path, user_id):
    sample_id = ObjectId()
    sample_id_2 = ObjectId()
    sample_item_id = "test_sample"
    sample_item_id_2 = "test_sample_2"

    sample_data = {
        "_id": sample_id,
        "item_id": sample_item_id,
        "name": "Test Sample",
        "type": "samples",
        "refcode": "test:ABCDEF",
        "relationships": [{"type": "samples", "immutable_id": sample_id_2}],
        "creator_ids": [user_id],
    }

    sample_data_2 = {
        "_id": sample_id_2,
        "item_id": sample_item_id_2,
        "name": "Test Sample",
        "type": "samples",
        "refcode": "test:ABCDEF2",
        "creator_ids": [user_id],
    }

    database.items.insert_one(sample_data)
    database.items.insert_one(sample_data_2)

    output_path = tmp_path / "test_samples.eln"

    try:
        create_eln_file(output_path, item_id=sample_item_id, related_item_ids=[sample_item_id_2])
        assert output_path.exists()

        with zipfile.ZipFile(output_path, "r") as zf:
            files = zf.namelist()

            assert f"{sample_item_id}/ro-crate-metadata.json" in files

            with zf.open(f"{sample_item_id}/ro-crate-metadata.json") as f:
                ro_crate = json.load(f)
                assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"

            try:
                with zf.open(f"{sample_item_id}/{sample_item_id}/metadata.json") as f:
                    sample_metadata = json.load(f)
                    assert sample_metadata["item_id"] == sample_item_id
                    assert sample_metadata["name"] == "Test Sample"

                with zf.open(f"{sample_item_id}/{sample_item_id_2}/metadata.json") as f:
                    sample_metadata = json.load(f)
                    assert sample_metadata["item_id"] == sample_item_id_2

            except KeyError:
                pytest.fail(f"Metadata file for {sample_item_id} not found in ELN file: {files}")

    finally:
        database.items.delete_one({"_id": sample_id})
        database.items.delete_one({"_id": sample_id_2})


def test_create_eln_file_collection(database, tmp_path, user_id):
    collection_id = "test_export"
    collection_data = {
        "_id": ObjectId(),
        "collection_id": collection_id,
        "title": "Export Test Collection",
        "creator_ids": [user_id],
    }

    sample_id = ObjectId()
    sample_data = {
        "_id": sample_id,
        "item_id": "test_sample",
        "name": "Test Sample",
        "refcode": "test:test123",
        "type": "samples",
        "relationships": [{"type": "collections", "immutable_id": collection_data["_id"]}],
        "creator_ids": [user_id],
    }

    cell_id = ObjectId()
    cell_data = {
        "_id": cell_id,
        "item_id": "test_cell",
        "name": "Test Cell",
        "type": "cells",
        "relationships": [{"type": "collections", "immutable_id": collection_data["_id"]}],
        "creator_ids": [user_id],
    }

    database.collections.insert_one(collection_data)
    database.items.insert_one(sample_data)
    database.items.insert_one(cell_data)

    output_path = tmp_path / "test.eln"

    try:
        create_eln_file(output_path, collection_id)
        assert output_path.exists()

        with zipfile.ZipFile(output_path, "r") as zf:
            files = zf.namelist()

            assert f"{collection_id}/ro-crate-metadata.json" in files, files
            assert f"{collection_id}/test_sample/metadata.json" in files, files

            with zf.open(f"{collection_id}/ro-crate-metadata.json") as f:
                ro_crate = json.load(f)
                assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"

            with zf.open(f"{collection_id}/test_sample/metadata.json") as f:
                sample_metadata = json.load(f)
                assert sample_metadata["item_id"] == "test_sample"
                assert sample_metadata["name"] == "Test Sample"

            with zf.open(f"{collection_id}/test_cell/metadata.json") as f:
                cell_metadata = json.load(f)
                assert cell_metadata["item_id"] == "test_cell"
                assert cell_metadata["name"] == "Test Cell"

    finally:
        database.collections.delete_one({"collection_id": collection_id})
        database.items.delete_one({"_id": sample_id})
        database.items.delete_one({"_id": cell_id})


def test_create_eln_file_collection_not_found(tmp_path):
    """Test error when collection not found."""
    output_file = tmp_path / "test.eln"
    with pytest.raises(ValueError, match="Collection .* not found"):
        create_eln_file("nonexistent_collection", str(output_file))
