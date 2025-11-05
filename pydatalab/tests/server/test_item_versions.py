"""Tests for item version control endpoints."""

import pytest
from bson import ObjectId


@pytest.fixture
def sample_with_version(client, user_id):
    """Create and insert a sample for version testing."""
    from pydatalab.models import Sample
    from pydatalab.models.utils import generate_unique_refcode
    from pydatalab.mongo import flask_mongo

    refcode = generate_unique_refcode()
    sample = Sample(
        **{
            "item_id": "version_test_sample",
            "name": "Version Test Sample",
            "description": "Initial description",
            "date": "2024-01-01",
            "refcode": refcode,
            "creator_ids": [user_id],
            "version": 1,
            "synthesis_description": "Initial synthesis",
        }
    )
    flask_mongo.db.items.insert_one(sample.dict(exclude_unset=False))

    yield sample

    # Cleanup
    flask_mongo.db.items.delete_one({"refcode": refcode})
    flask_mongo.db.item_versions.delete_many({"refcode": refcode})
    flask_mongo.db.version_counters.delete_one({"refcode": refcode})


class TestSaveVersion:
    """Tests for the save_version endpoint."""

    def test_save_version_success(self, client, sample_with_version):
        """Test successfully saving a version."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.post(f"/items/{refcode}/save-version/")

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "version_number" in response.json
        assert response.json["version_number"] == 1

    def test_save_version_multiple_times(self, client, sample_with_version):
        """Test that version numbers increment atomically."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save first version
        response1 = client.post(f"/items/{refcode}/save-version/")
        assert response1.status_code == 200
        version1 = response1.json["version_number"]

        # Save second version
        response2 = client.post(f"/items/{refcode}/save-version/")
        assert response2.status_code == 200
        version2 = response2.json["version_number"]

        # Save third version
        response3 = client.post(f"/items/{refcode}/save-version/")
        assert response3.status_code == 200
        version3 = response3.json["version_number"]

        # Ensure versions increment
        assert version2 == version1 + 1
        assert version3 == version2 + 1

    def test_save_version_with_full_refcode(self, client, sample_with_version):
        """Test saving version with full prefixed refcode."""
        refcode = sample_with_version.refcode
        response = client.post(f"/items/{refcode}/save-version/")

        assert response.status_code == 200
        assert response.json["status"] == "success"

    def test_save_version_nonexistent_item(self, client):
        """Test saving version for non-existent item."""
        response = client.post("/items/nonexistent/save-version/")

        assert response.status_code == 404
        assert response.json["status"] == "error"


class TestListVersions:
    """Tests for the list_versions endpoint."""

    def test_list_versions_empty(self, client, sample_with_version):
        """Test listing versions when none exist."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.get(f"/items/{refcode}/versions/")

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert response.json["versions"] == []

    def test_list_versions_after_saves(self, client, sample_with_version):
        """Test listing versions after saving multiple versions."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save three versions
        client.post(f"/items/{refcode}/save-version/")
        client.post(f"/items/{refcode}/save-version/")
        client.post(f"/items/{refcode}/save-version/")

        # List versions
        response = client.get(f"/items/{refcode}/versions/")

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert len(response.json["versions"]) == 3

        # Check that versions are sorted in descending order (newest first)
        versions = response.json["versions"]
        assert versions[0]["version_number"] == 3
        assert versions[1]["version_number"] == 2
        assert versions[2]["version_number"] == 1

    def test_list_versions_contains_metadata(self, client, sample_with_version):
        """Test that listed versions contain required metadata."""
        refcode = sample_with_version.refcode.split(":")[1]
        client.post(f"/items/{refcode}/save-version/")

        response = client.get(f"/items/{refcode}/versions/")
        version = response.json["versions"][0]

        assert "_id" in version
        assert "timestamp" in version
        assert "user" in version
        assert "software_version" in version
        assert "version_number" in version
        assert "action" in version

    def test_list_versions_includes_action_field(self, client, sample_with_version):
        """Test that listed versions include the action field."""
        refcode = sample_with_version.refcode.split(":")[1]
        client.post(f"/items/{refcode}/save-version/")

        response = client.get(f"/items/{refcode}/versions/")
        version = response.json["versions"][0]

        # Should include action field in list response
        assert "action" in version
        assert version["action"] == "manual_save"


class TestGetVersion:
    """Tests for the get_version endpoint."""

    def test_get_version_success(self, client, sample_with_version):
        """Test successfully retrieving a specific version."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # List versions to get the version ID
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]

        # Get the specific version
        response = client.get(f"/items/{refcode}/versions/{version_id}/")

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert response.json["version"]["_id"] == version_id
        assert response.json["version"]["refcode"] == sample_with_version.refcode
        assert "data" in response.json["version"]
        assert response.json["version"]["data"]["name"] == "Version Test Sample"

    def test_get_version_invalid_id(self, client, sample_with_version):
        """Test getting version with invalid ID format."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.get(f"/items/{refcode}/versions/invalid_id/")

        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert "Invalid version_id" in response.json["message"]

    def test_get_version_nonexistent(self, client, sample_with_version):
        """Test getting non-existent version."""
        refcode = sample_with_version.refcode.split(":")[1]
        fake_id = str(ObjectId())
        response = client.get(f"/items/{refcode}/versions/{fake_id}/")

        assert response.status_code == 404
        assert response.json["status"] == "error"
        assert "not found" in response.json["message"].lower()


class TestCompareVersions:
    """Tests for the compare_versions endpoint."""

    def test_compare_versions_success(self, client, sample_with_version):
        """Test successfully comparing two versions."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Modify the item
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode},
            {"$set": {"description": "Modified description", "version": 2}},
        )

        # Save second version
        client.post(f"/items/{refcode}/save-version/")

        # Get version IDs
        list_response = client.get(f"/items/{refcode}/versions/")
        versions = list_response.json["versions"]
        v1_id = versions[1]["_id"]  # Older version
        v2_id = versions[0]["_id"]  # Newer version

        # Compare versions
        response = client.get(f"/items/{refcode}/compare-versions/?v1={v1_id}&v2={v2_id}")

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "diff" in response.json
        assert "v1_version_number" in response.json
        assert "v2_version_number" in response.json
        assert response.json["v1_version_number"] == 1
        assert response.json["v2_version_number"] == 2

    def test_compare_versions_missing_parameters(self, client, sample_with_version):
        """Test comparing versions with missing parameters."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Missing v2
        response = client.get(f"/items/{refcode}/compare-versions/?v1=some_id")
        assert response.status_code == 400
        assert "Both v1 and v2 must be provided" in response.json["message"]

        # Missing v1
        response = client.get(f"/items/{refcode}/compare-versions/?v2=some_id")
        assert response.status_code == 400

    def test_compare_versions_invalid_id(self, client, sample_with_version):
        """Test comparing versions with invalid ID format."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.get(f"/items/{refcode}/compare-versions/?v1=invalid&v2=invalid")

        assert response.status_code == 400
        assert "Invalid version ID format" in response.json["message"]

    def test_compare_versions_detects_changes(self, client, sample_with_version):
        """Test that compare_versions properly detects changes using DeepDiff."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Make multiple types of changes
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode},
            {
                "$set": {
                    "description": "Changed description",
                    "synthesis_description": "Changed synthesis",
                    "version": 2,
                }
            },
        )

        # Save second version
        client.post(f"/items/{refcode}/save-version/")

        # Compare
        list_response = client.get(f"/items/{refcode}/versions/")
        versions = list_response.json["versions"]
        response = client.get(
            f"/items/{refcode}/compare-versions/?v1={versions[1]['_id']}&v2={versions[0]['_id']}"
        )

        assert response.status_code == 200
        diff = response.json["diff"]

        # DeepDiff should detect the changes
        # The exact structure depends on DeepDiff's output format
        assert diff  # Diff should not be empty


class TestRestoreVersion:
    """Tests for the restore_version endpoint."""

    def test_restore_version_success(self, client, sample_with_version):
        """Test successfully restoring to a previous version."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Modify the item
        original_description = sample_with_version.description
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode},
            {"$set": {"description": "Modified description", "version": 2}},
        )

        # Get version ID
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]

        # Restore to the previous version
        response = client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": version_id}
        )

        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "restored_version" in response.json
        assert "new_version_number" in response.json

        # Verify the item was restored
        item = flask_mongo.db.items.find_one({"refcode": full_refcode})
        assert item["description"] == original_description

    def test_restore_version_creates_snapshot(self, client, sample_with_version):
        """Test that restore creates a version snapshot with restored data."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save version and modify
        client.post(f"/items/{refcode}/save-version/")
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Modified", "version": 2}}
        )

        # Get version to restore
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]

        # Restore
        client.post(f"/items/{refcode}/restore-version/", json={"version_id": version_id})

        # Check that a restored version snapshot was created
        list_response = client.get(f"/items/{refcode}/versions/")
        versions = list_response.json["versions"]

        # Should have 2 versions now: original save + restored snapshot
        assert len(versions) == 2

    def test_restore_version_protects_fields(self, client, sample_with_version):
        """Test that protected fields are not overwritten during restore."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Get original protected field values
        original_item = flask_mongo.db.items.find_one({"refcode": full_refcode})
        original_refcode = original_item["refcode"]
        original_id = original_item["_id"]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Modify non-protected field
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Modified", "version": 2}}
        )

        # Get version and restore
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]
        client.post(f"/items/{refcode}/restore-version/", json={"version_id": version_id})

        # Verify protected fields unchanged
        restored_item = flask_mongo.db.items.find_one({"refcode": full_refcode})
        assert restored_item["refcode"] == original_refcode
        assert restored_item["_id"] == original_id

    def test_restore_version_invalid_type_change(self, client, sample_with_version):
        """Test that restoring fails if type would change."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Manually change the type in the current item
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"type": "cells", "version": 2}}
        )

        # Try to restore (should fail because old type is "samples")
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]
        response = client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": version_id}
        )

        assert response.status_code == 400
        assert "different type" in response.json["message"].lower()

    def test_restore_version_missing_version_id(self, client, sample_with_version):
        """Test restoring without providing version_id."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.post(f"/items/{refcode}/restore-version/", json={})

        assert response.status_code == 400
        assert "version_id must be provided" in response.json["message"]

    def test_restore_version_invalid_id(self, client, sample_with_version):
        """Test restoring with invalid version ID."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.post(f"/items/{refcode}/restore-version/", json={"version_id": "invalid"})

        assert response.status_code == 400
        assert "Invalid version_id" in response.json["message"]

    def test_restore_version_nonexistent(self, client, sample_with_version):
        """Test restoring non-existent version."""
        refcode = sample_with_version.refcode.split(":")[1]
        fake_id = str(ObjectId())
        response = client.post(f"/items/{refcode}/restore-version/", json={"version_id": fake_id})

        assert response.status_code == 404
        assert "not found" in response.json["message"].lower()

    def test_restore_version_increments_version_number(self, client, sample_with_version):
        """Test that restore increments the item version number."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save version
        client.post(f"/items/{refcode}/save-version/")

        # Modify
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Modified", "version": 2}}
        )

        # Restore
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]
        restore_response = client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": version_id}
        )

        new_version = restore_response.json["new_version_number"]

        # Check that item version was updated
        item = flask_mongo.db.items.find_one({"refcode": full_refcode})
        assert item["version"] == new_version
        assert item["version"] > 1


class TestDeleteVersion:
    """Tests for the delete_version endpoint."""

    def test_delete_version_success(self, client, sample_with_version):
        """Test successfully deleting a version."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Get version ID
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]

        # Delete the version
        response = client.delete(f"/items/{refcode}/versions/{version_id}/")

        assert response.status_code == 200
        assert response.json["status"] == "success"

        # Verify it's gone
        list_response = client.get(f"/items/{refcode}/versions/")
        assert len(list_response.json["versions"]) == 0

    def test_delete_version_nonexistent(self, client, sample_with_version):
        """Test deleting non-existent version."""
        refcode = sample_with_version.refcode.split(":")[1]
        fake_id = str(ObjectId())
        response = client.delete(f"/items/{refcode}/versions/{fake_id}/")

        assert response.status_code == 404
        assert response.json["status"] == "error"

    def test_delete_version_invalid_id(self, client, sample_with_version):
        """Test deleting with invalid ID format."""
        refcode = sample_with_version.refcode.split(":")[1]
        response = client.delete(f"/items/{refcode}/versions/invalid_id/")

        assert response.status_code == 400
        assert "Invalid version_id" in response.json["message"]


class TestAutoVersioning:
    """Tests for automatic versioning on save_item."""

    def test_save_item_creates_version(self, client, sample_with_version):
        """Test that saving an item automatically creates a version."""

        item_id = sample_with_version.item_id
        refcode_short = sample_with_version.refcode.split(":")[1]

        # Modify and save the item using save-item endpoint
        item_data = sample_with_version.dict(exclude_unset=False)
        item_data["description"] = "Updated via save-item"

        response = client.post("/save-item/", json={"item_id": item_id, "data": item_data})

        assert response.status_code == 200

        # Check that a version was created
        list_response = client.get(f"/items/{refcode_short}/versions/")
        assert len(list_response.json["versions"]) >= 1

        # Check that the latest version has action="manual_save"
        latest_version = list_response.json["versions"][0]
        full_version = client.get(f"/items/{refcode_short}/versions/{latest_version['_id']}/").json[
            "version"
        ]
        assert full_version["action"] == "manual_save"

    def test_save_item_increments_version(self, client, sample_with_version):
        """Test that save_item increments the version field."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode
        original_version = sample_with_version.version

        # Save the item
        item_data = sample_with_version.dict(exclude_unset=False)
        item_data["description"] = "Updated"
        client.post("/save-item/", json={"item_id": sample_with_version.item_id, "data": item_data})

        # Check that version incremented
        item = flask_mongo.db.items.find_one({"refcode": refcode})
        assert item["version"] == original_version + 1


class TestActionFields:
    """Tests specifically for validating action field values across different operations."""

    def test_manual_save_version_endpoint_action(self, client, sample_with_version):
        """Test that manual save_version endpoint creates action='manual_save'."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Manually save a version via save-version endpoint
        client.post(f"/items/{refcode}/save-version/")

        # Check the version action in list
        list_response = client.get(f"/items/{refcode}/versions/")
        version = list_response.json["versions"][0]

        assert version["action"] == "manual_save"
        # Manual saves should not have restored_from_version
        assert version.get("restored_from_version") is None

    def test_save_item_endpoint_creates_manual_save_action(self, client, sample_with_version):
        """Test that save_item endpoint creates action='manual_save' (user-triggered save)."""
        refcode_short = sample_with_version.refcode.split(":")[1]

        # Save via save-item endpoint (user clicking save button)
        item_data = sample_with_version.dict(exclude_unset=False)
        item_data["description"] = "Updated via save-item"
        client.post("/save-item/", json={"item_id": sample_with_version.item_id, "data": item_data})

        # Check the version action
        list_response = client.get(f"/items/{refcode_short}/versions/")
        version = list_response.json["versions"][0]

        # save_item should create manual_save action (user-triggered)
        assert version["action"] == "manual_save"

    def test_restored_action_and_reference(self, client, sample_with_version):
        """Test that restore creates action='restored' with restored_from_version."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Modify
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Modified", "version": 2}}
        )

        # Get version to restore
        list_response = client.get(f"/items/{refcode}/versions/")
        version_to_restore_id = list_response.json["versions"][0]["_id"]

        # Restore
        client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": version_to_restore_id}
        )

        # Check restored version in list
        list_response = client.get(f"/items/{refcode}/versions/")
        restored_version = list_response.json["versions"][0]

        assert restored_version["action"] == "restored"
        assert restored_version["restored_from_version"] == version_to_restore_id

    def test_restored_version_snapshot_contains_restored_data(self, client, sample_with_version):
        """Test that the version snapshot created by restore contains the restored data, not pre-restore data."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode
        original_description = sample_with_version.description

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Modify the item
        modified_description = "Modified description"
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": modified_description, "version": 2}}
        )

        # Get version to restore from
        list_response = client.get(f"/items/{refcode}/versions/")
        version_to_restore_id = list_response.json["versions"][0]["_id"]

        # Restore
        client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": version_to_restore_id}
        )

        # Get the restored version snapshot
        list_response = client.get(f"/items/{refcode}/versions/")
        restored_version_id = list_response.json["versions"][0]["_id"]

        get_response = client.get(f"/items/{refcode}/versions/{restored_version_id}/")
        restored_snapshot = get_response.json["version"]["data"]

        # The snapshot should contain the RESTORED data (original_description)
        # NOT the pre-restore data (modified_description)
        assert restored_snapshot["description"] == original_description

    def test_action_audit_trail_complete(self, client, sample_with_version):
        """Test complete audit trail with multiple saves and restore."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Manual save via save-version endpoint (v1)
        client.post(f"/items/{refcode}/save-version/")

        # Modify and save via save-item (v2)
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Second version", "version": 2}}
        )
        item_data = flask_mongo.db.items.find_one({"refcode": full_refcode})
        # Convert ObjectId to string for JSON serialization
        item_data["_id"] = str(item_data["_id"])
        if "immutable_id" in item_data:
            item_data["immutable_id"] = str(item_data["immutable_id"])
        client.post("/save-item/", json={"item_id": sample_with_version.item_id, "data": item_data})

        # Get v1 to restore
        list_response = client.get(f"/items/{refcode}/versions/")
        versions = list_response.json["versions"]
        v1_id = versions[1]["_id"]  # Second in list (sorted desc)

        # Restore to v1 (creates v3)
        client.post(f"/items/{refcode}/restore-version/", json={"version_id": v1_id})

        # Check all versions
        list_response = client.get(f"/items/{refcode}/versions/")
        all_versions = list_response.json["versions"]

        # Should have 3 versions
        assert len(all_versions) == 3

        # v3 (newest): restored
        assert all_versions[0]["action"] == "restored"
        assert all_versions[0]["restored_from_version"] == v1_id

        # v2: manual_save (from save-item)
        assert all_versions[1]["action"] == "manual_save"
        assert all_versions[1].get("restored_from_version") is None

        # v1 (oldest): manual_save (from save-version)
        assert all_versions[2]["action"] == "manual_save"
        assert all_versions[2].get("restored_from_version") is None


class TestVersionCounter:
    """Tests for atomic version counter functionality."""

    def test_version_counter_atomic_increment(self, client, sample_with_version):
        """Test that version counter increments atomically."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save multiple versions and verify each gets unique sequential number
        version_numbers = []
        for i in range(5):
            response = client.post(f"/items/{refcode}/save-version/")
            version_numbers.append(response.json["version_number"])

        # All version numbers should be unique and sequential
        assert version_numbers == [1, 2, 3, 4, 5]

        # Check counter document
        counter = flask_mongo.db.version_counters.find_one({"refcode": full_refcode})
        assert counter["counter"] == 5

    def test_version_counter_created_on_first_save(self, client, sample_with_version):
        """Test that version counter is created on first save."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Ensure no counter exists
        flask_mongo.db.version_counters.delete_one({"refcode": full_refcode})

        # Save first version
        response = client.post(f"/items/{refcode}/save-version/")
        assert response.json["version_number"] == 1

        # Check counter was created
        counter = flask_mongo.db.version_counters.find_one({"refcode": full_refcode})
        assert counter is not None
        assert counter["counter"] == 1


class TestPermissions:
    """Tests for version control permissions."""

    def test_restore_requires_write_permission(self, another_client, sample_with_version):
        """Test that restoring requires write permissions on the item."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version with the owner
        # (sample_with_version is created by user_id, another_client uses another_user_id)

        # Try to restore with different user (should fail due to permissions)
        fake_version_id = str(ObjectId())
        response = another_client.post(
            f"/items/{refcode}/restore-version/", json={"version_id": fake_version_id}
        )

        # Should fail because another_client doesn't have access to this item
        assert response.status_code == 404
        assert "not found or insufficient permissions" in response.json["message"].lower()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_refcode_with_and_without_prefix(self, client, sample_with_version):
        """Test that endpoints work with both short and full refcodes."""
        short_refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save with short refcode
        response1 = client.post(f"/items/{short_refcode}/save-version/")
        assert response1.status_code == 200

        # Save with full refcode
        response2 = client.post(f"/items/{full_refcode}/save-version/")
        assert response2.status_code == 200

        # Both should work with list
        response3 = client.get(f"/items/{short_refcode}/versions/")
        response4 = client.get(f"/items/{full_refcode}/versions/")

        assert response3.status_code == 200
        assert response4.status_code == 200
        assert len(response3.json["versions"]) == 2
        assert len(response4.json["versions"]) == 2

    def test_version_metadata_complete(self, client, sample_with_version):
        """Test that saved versions contain all required metadata."""
        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Get the version
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]
        response = client.get(f"/items/{refcode}/versions/{version_id}/")

        version = response.json["version"]

        # Check all required fields present
        assert "refcode" in version
        assert "version_number" in version
        assert "timestamp" in version
        assert "action" in version
        assert "user" in version
        assert "software_version" in version
        assert "data" in version

        # Check user info structure
        assert "id" in version["user"]
        assert "display_name" in version["user"]
        assert "email" in version["user"]

    def test_version_snapshot_is_complete(self, client, sample_with_version):
        """Test that version snapshot contains complete item data."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Get current item
        original_item = flask_mongo.db.items.find_one({"refcode": full_refcode})

        # Save version
        client.post(f"/items/{refcode}/save-version/")

        # Get version and check data matches original
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]
        version_response = client.get(f"/items/{refcode}/versions/{version_id}/")

        snapshot = version_response.json["version"]["data"]

        # Key fields should match
        assert snapshot["name"] == original_item["name"]
        assert snapshot["description"] == original_item["description"]
        assert snapshot["item_id"] == original_item["item_id"]
        assert snapshot["refcode"] == original_item["refcode"]


class TestUserIdField:
    """Tests for the user_id field in version documents (hybrid storage approach)."""

    def test_version_includes_user_id_field(self, client, sample_with_version):
        """Test that saved versions include both user snapshot and user_id ObjectId."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Get the version document directly from database
        version_doc = flask_mongo.db.item_versions.find_one(
            {"refcode": sample_with_version.refcode}
        )

        # Check user snapshot exists (for fast display)
        assert "user" in version_doc
        assert version_doc["user"] is not None
        assert "id" in version_doc["user"]
        assert "display_name" in version_doc["user"]
        assert "email" in version_doc["user"]

        # Check user_id ObjectId exists (for efficient querying)
        assert "user_id" in version_doc
        assert version_doc["user_id"] is not None
        # Verify it's an ObjectId, not a string
        assert isinstance(version_doc["user_id"], ObjectId)

    def test_user_id_matches_user_snapshot_id(self, client, sample_with_version):
        """Test that user_id ObjectId matches the string ID in user snapshot."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]

        # Save a version
        client.post(f"/items/{refcode}/save-version/")

        # Get version document
        version_doc = flask_mongo.db.item_versions.find_one(
            {"refcode": sample_with_version.refcode}
        )

        # user_id ObjectId should match user.id string
        assert str(version_doc["user_id"]) == version_doc["user"]["id"]

    def test_restored_version_includes_user_id(self, client, sample_with_version):
        """Test that restored versions also include user_id field."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]
        full_refcode = sample_with_version.refcode

        # Save initial version
        client.post(f"/items/{refcode}/save-version/")

        # Modify the item
        flask_mongo.db.items.update_one(
            {"refcode": full_refcode}, {"$set": {"description": "Modified", "version": 2}}
        )

        # Get version to restore
        list_response = client.get(f"/items/{refcode}/versions/")
        version_id = list_response.json["versions"][0]["_id"]

        # Restore
        client.post(f"/items/{refcode}/restore-version/", json={"version_id": version_id})

        # Get the restored version document
        restored_version = flask_mongo.db.item_versions.find_one(
            {"refcode": full_refcode, "action": "restored"}
        )

        # Check both user fields exist
        assert "user" in restored_version
        assert "user_id" in restored_version
        assert isinstance(restored_version["user_id"], ObjectId)
        assert str(restored_version["user_id"]) == restored_version["user"]["id"]

    def test_query_versions_by_user_id(self, client, sample_with_version, user_id):
        """Test that we can efficiently query versions by user_id ObjectId."""
        from pydatalab.mongo import flask_mongo

        refcode = sample_with_version.refcode.split(":")[1]

        # Save multiple versions
        client.post(f"/items/{refcode}/save-version/")
        client.post(f"/items/{refcode}/save-version/")
        client.post(f"/items/{refcode}/save-version/")

        # Query by user_id ObjectId (this uses the index)
        versions_by_user = list(flask_mongo.db.item_versions.find({"user_id": user_id}))

        # Should find all 3 versions
        assert len(versions_by_user) >= 3

        # All should belong to the same user
        for version in versions_by_user:
            assert version["user_id"] == user_id
            assert version["user"]["id"] == str(user_id)
