import json
import zipfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from bson import ObjectId

from pydatalab.export_utils import (
    _convert_objectids_in_dict,
    create_eln_file,
    generate_ro_crate_metadata,
)


class TestExportUtils:
    def test_convert_objectids_in_dict(self):
        """Test ObjectId and datetime conversion in dictionaries."""
        test_id = ObjectId()
        test_date = datetime.now(tz=timezone.utc)

        input_dict = {
            "id": test_id,
            "date": test_date,
            "nested": {
                "nested_id": test_id,
                "nested_date": test_date,
            },
            "list": [test_id, test_date],
            "string": "test",
        }

        result = _convert_objectids_in_dict(input_dict)

        assert result["id"] == str(test_id)
        assert result["date"] == test_date.isoformat()
        assert result["nested"]["nested_id"] == str(test_id)
        assert result["nested"]["nested_date"] == test_date.isoformat()
        assert result["list"][0] == str(test_id)
        assert result["list"][1] == test_date.isoformat()
        assert result["string"] == "test"

    def test_generate_ro_crate_metadata(self):
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

        with patch("pydatalab.export_utils.flask_mongo.db.files.find_one") as mock_find:
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

    def test_create_eln_file(self, database, tmp_path, user_id):
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
            "type": "samples",
            "relationships": [{"type": "collections", "immutable_id": collection_data["_id"]}],
            "creator_ids": [user_id],
        }

        database.collections.insert_one(collection_data)
        database.items.insert_one(sample_data)

        output_path = tmp_path / "test.eln"

        try:
            create_eln_file(str(output_path), collection_id)
            assert output_path.exists()

            with zipfile.ZipFile(output_path, "r") as zf:
                files = zf.namelist()

                assert f"{collection_id}/ro-crate-metadata.json" in files
                assert f"{collection_id}/test_sample/metadata.json" in files

                with zf.open(f"{collection_id}/ro-crate-metadata.json") as f:
                    ro_crate = json.load(f)
                    assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"

                with zf.open(f"{collection_id}/test_sample/metadata.json") as f:
                    sample_metadata = json.load(f)
                    assert sample_metadata["item_id"] == "test_sample"
                    assert sample_metadata["name"] == "Test Sample"

        finally:
            database.collections.delete_one({"collection_id": collection_id})
            database.items.delete_one({"_id": sample_id})

    def test_create_eln_file_collection_not_found(self, tmp_path):
        """Test error when collection not found."""
        output_file = tmp_path / "test.eln"
        with pytest.raises(ValueError, match="Collection .* not found"):
            create_eln_file("nonexistent_collection", str(output_file))
