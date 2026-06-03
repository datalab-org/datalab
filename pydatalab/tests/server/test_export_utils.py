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
            "refcode": "sample1",
            "date": datetime.now(tz=timezone.utc),
            "file_ObjectIds": ["507f1f77bcf86cd799439011"],
        },
        {
            "item_id": "sample2",
            "name": "Sample 2",
            "refcode": "sample2",
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


def _people_sharing_items(num_items, creator_id):
    """Build ``num_items`` child items that all share a single creator."""
    return [
        {
            "item_id": f"sample{i}",
            "name": f"Sample {i}",
            "refcode": f"test:CODE{i}",
            "creators": [{"display_name": "Shared Creator", "immutable_id": creator_id}],
        }
        for i in range(num_items)
    ]


def test_ro_crate_people_not_duplicated():
    """A creator shared across many items should appear exactly once in the graph."""
    creator_id = ObjectId()
    child_items = _people_sharing_items(3, creator_id)

    metadata = generate_ro_crate_metadata({"collection_id": "c", "title": "C"}, child_items)

    people = [node for node in metadata["@graph"] if node.get("@type") == "Person"]
    assert len(people) == 1
    assert people[0]["@id"] == f"./people/{creator_id}"

    # The single person node should still be referenced as an author by every item.
    for item in child_items:
        dataset = next(n for n in metadata["@graph"] if n["@id"] == f"./{item['item_id']}/")
        assert dataset["authors"] == [{"@id": f"./people/{creator_id}"}]


def test_ro_crate_software_and_action_not_duplicated_per_item():
    """The ``SoftwareApplication`` and ``CreateAction`` nodes describe the export
    as a whole, so they must appear once regardless of the number of items."""
    child_items = _people_sharing_items(4, ObjectId())

    metadata = generate_ro_crate_metadata({"collection_id": "c", "title": "C"}, child_items)

    software = [n for n in metadata["@graph"] if n.get("@type") == "SoftwareApplication"]
    actions = [n for n in metadata["@graph"] if n.get("@type") == "CreateAction"]
    assert len(software) == 1
    assert len(actions) == 1

    # No graph node should be emitted twice (would be invalid RO-Crate).
    ids = [n["@id"] for n in metadata["@graph"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("primary_key", ["item_id", "refcode"])
def test_ro_crate_primary_key_switch(primary_key):
    """The folder/``@id`` key can be switched between ``item_id`` and ``refcode``."""
    child_items = [
        {
            "item_id": "sample_a",
            "name": "Sample A",
            "refcode": "test:REFA",
            "creators": [],
        }
    ]

    metadata = generate_ro_crate_metadata(
        {"collection_id": "c", "title": "C"}, child_items, primary_key=primary_key
    )

    expected_key = child_items[0][primary_key]
    other_key = child_items[0]["refcode" if primary_key == "item_id" else "item_id"]

    dataset_ids = [n["@id"] for n in metadata["@graph"] if n.get("@type") == "Dataset"]
    assert f"./{expected_key}/" in dataset_ids
    if expected_key != other_key:
        assert f"./{other_key}/" not in dataset_ids

    # The per-item metadata.json file should hang off the same key.
    assert any(
        n["@id"] == f"./{expected_key}/metadata.json"
        for n in metadata["@graph"]
        if n.get("@type") == "File"
    )

    # The stable identifier is always the refcode, independent of the folder key.
    dataset = next(n for n in metadata["@graph"] if n["@id"] == f"./{expected_key}/")
    assert dataset["identifier"] == "test:REFA"


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
        "creators": [{"display_name": "Test User", "immutable_id": user_id}],
    }

    sample_data_2 = {
        "_id": sample_id_2,
        "item_id": sample_item_id_2,
        "name": "Test Sample",
        "type": "samples",
        "refcode": "test:ABCDEF2",
        "creator_ids": [user_id],
        "creators": [{"display_name": "Test User", "immutable_id": user_id}],
    }

    database.items.insert_one(sample_data)
    database.items.insert_one(sample_data_2)

    output_path = tmp_path / "test_samples.eln"

    try:
        create_eln_file(
            output_path,
            item_id=sample_item_id,
            related_item_ids=[sample_item_id_2],
            primary_key="refcode",
        )
        assert output_path.exists()

        with zipfile.ZipFile(output_path, "r") as zf:
            files = zf.namelist()

            assert f"{sample_data['refcode']}/ro-crate-metadata.json" in files

            with zf.open(f"{sample_data['refcode']}/ro-crate-metadata.json") as f:
                ro_crate = json.load(f)
                assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"

            try:
                with zf.open(
                    f"{sample_data['refcode']}/{sample_data['refcode']}/metadata.json"
                ) as f:
                    sample_metadata = json.load(f)
                    assert sample_metadata["item_id"] == sample_item_id
                    assert sample_metadata["name"] == "Test Sample"

                with zf.open(
                    f"{sample_data['refcode']}/{sample_data_2['refcode']}/metadata.json"
                ) as f:
                    sample_metadata = json.load(f)
                    assert sample_metadata["item_id"] == sample_item_id_2

            except KeyError:
                pytest.fail(f"Metadata file for {sample_item_id} not found in ELN file: {files}")

    finally:
        database.items.delete_one({"_id": sample_id})
        database.items.delete_one({"_id": sample_id_2})


def test_create_eln_file_items_default_item_id_key(database, tmp_path, user_id):
    """By default (no ``primary_key``) exports key item folders by ``item_id``,
    which is the more human-friendly layout preferred for manual exports."""
    sample_id = ObjectId()
    sample_id_2 = ObjectId()
    sample_item_id = "human_sample"
    sample_item_id_2 = "human_sample_2"

    sample_data = {
        "_id": sample_id,
        "item_id": sample_item_id,
        "name": "Test Sample",
        "type": "samples",
        "refcode": "test:HUMAN1",
        "relationships": [{"type": "samples", "immutable_id": sample_id_2}],
        "creator_ids": [user_id],
        "creators": [{"display_name": "Test User", "immutable_id": user_id}],
    }

    sample_data_2 = {
        "_id": sample_id_2,
        "item_id": sample_item_id_2,
        "name": "Test Sample 2",
        "type": "samples",
        "refcode": "test:HUMAN2",
        "creator_ids": [user_id],
        "creators": [{"display_name": "Test User", "immutable_id": user_id}],
    }

    database.items.insert_one(sample_data)
    database.items.insert_one(sample_data_2)

    output_path = tmp_path / "human_samples.eln"

    try:
        # No primary_key argument -> defaults to "item_id"
        create_eln_file(output_path, item_id=sample_item_id, related_item_ids=[sample_item_id_2])
        assert output_path.exists()

        # The root folder is still the main item's refcode, but item folders inside
        # are keyed by item_id, not refcode.
        root = sample_data["refcode"]
        with zipfile.ZipFile(output_path, "r") as zf:
            files = zf.namelist()

            assert f"{root}/{sample_item_id}/metadata.json" in files
            assert f"{root}/{sample_item_id_2}/metadata.json" in files

            # The refcode-keyed paths must NOT be present under the default.
            assert f"{root}/{sample_data['refcode']}/metadata.json" not in files
            assert f"{root}/{sample_data_2['refcode']}/metadata.json" not in files

            with zf.open(f"{root}/{sample_item_id}/metadata.json") as f:
                assert json.load(f)["item_id"] == sample_item_id

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
        "refcode": "test:cell123",
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
        create_eln_file(output_path, collection_id, primary_key="refcode")
        assert output_path.exists()

        with zipfile.ZipFile(output_path, "r") as zf:
            files = zf.namelist()

            assert f"{collection_id}/ro-crate-metadata.json" in files
            assert f"{collection_id}/{sample_data['refcode']}/metadata.json" in files

            with zf.open(f"{collection_id}/ro-crate-metadata.json") as f:
                ro_crate = json.load(f)
                assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"

            with zf.open(f"{collection_id}/{sample_data['refcode']}/metadata.json") as f:
                sample_metadata = json.load(f)
                assert sample_metadata["item_id"] == "test_sample"
                assert sample_metadata["name"] == "Test Sample"

            with zf.open(f"{collection_id}/{cell_data['refcode']}/metadata.json") as f:
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
