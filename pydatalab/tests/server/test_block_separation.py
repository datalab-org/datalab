"""Core verification tests for the separation of blocks into their own
`blocks`/`block_versions` collections.

These cover the two coexisting storage forms of an item's `blocks_obj` entry:
legacy *embedded* payloads (frozen in that form for life) and *referenced*
blocks (`{"immutable_id": ObjectId}` pointers, used for all newly created
blocks), plus the versioning/restore/reconciliation flows across them.
"""

import pytest
from bson import ObjectId


@pytest.fixture()
def sample_with_block(admin_client, default_sample_dict, random_string):
    """Create a fresh sample with one (referenced) comment block attached,
    returning `(sample_id, refcode, block_id)`."""
    sample_id = f"test_block_sep_{random_string[:10]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, response.json

    response = admin_client.post(
        "/add-data-block/",
        json={"block_type": "comment", "item_id": sample_id, "index": 0},
    )
    assert response.status_code == 200, response.json
    block_id = response.json["new_block_obj"]["block_id"]

    response = admin_client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200
    refcode = response.json["item_data"]["refcode"]

    yield sample_id, refcode, block_id

    admin_client.post("/delete-sample/", json={"item_id": sample_id})


def _get_item_data(client, sample_id):
    response = client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200, response.json
    return response.json["item_data"]


def _save_item(client, sample_id, item_data):
    response = client.post("/save-item/", json={"item_id": sample_id, "data": item_data})
    assert response.status_code == 200, response.json
    return response


def _insert_legacy_embedded_block(database, sample_id, block_id, comment="legacy comment"):
    """Simulate a pre-separation item by embedding a full block payload directly
    in the item document."""
    payload = {
        "blocktype": "comment",
        "block_id": block_id,
        "item_id": sample_id,
        "title": "Comment",
        "freeform_comment": comment,
    }
    result = database.items.update_one(
        {"item_id": sample_id},
        {"$set": {f"blocks_obj.{block_id}": payload}, "$push": {"display_order": block_id}},
    )
    assert result.modified_count == 1
    return payload


def test_new_block_is_referenced_and_reassembled(sample_with_block, admin_client, database):
    """A newly created block lands in `blocks` with a reference in the item, has
    no committed version yet, and API reads reassemble the full payload."""
    sample_id, _, block_id = sample_with_block

    stored_entry = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]
    assert set(stored_entry) == {"immutable_id"}

    block_doc = database.blocks.find_one({"_id": stored_entry["immutable_id"]})
    assert block_doc is not None
    assert block_doc["block_id"] == block_id
    assert block_doc["blocktype"] == "comment"
    assert block_doc["type"] == "blocks"
    assert block_doc["version"] == 0
    assert block_doc["data"]["blocktype"] == "comment"
    assert block_doc["data"]["block_id"] == block_id

    # No block version is committed at creation
    assert database.block_versions.count_documents({"block_id": block_id}) == 0

    # The API response keeps the pre-separation shape
    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][block_id]["blocktype"] == "comment"
    assert item_data["blocks_obj"][block_id]["block_id"] == block_id
    assert item_data["display_order"] == [block_id]


def test_summary_and_graph_resolve_referenced_blocks(sample_with_block, admin_client):
    """Summary block previews and the item graph report the blocktype of
    referenced blocks."""
    sample_id, _, block_id = sample_with_block

    response = admin_client.get("/samples/")
    assert response.status_code == 200
    entries = [s for s in response.json["samples"] if s["item_id"] == sample_id]
    assert len(entries) == 1
    assert entries[0]["nblocks"] == 1
    assert {b["blocktype"] for b in entries[0]["blocks"]} == {"comment"}

    response = admin_client.get(f"/item-graph/{sample_id}")
    assert response.status_code == 200
    block_nodes = [n for n in response.json["nodes"] if n["data"]["id"] == block_id]
    assert len(block_nodes) == 1
    assert block_nodes[0]["data"]["name"] == "comment"


def test_update_block_and_versioning_flow(sample_with_block, admin_client, database):
    """`update-block` only writes the live `blocks` doc; versions are cut by item
    snapshots (any entry point), de-duplicated when the payload is unchanged."""
    sample_id, refcode, block_id = sample_with_block

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]

    # Update the block: live doc is written, but no version is committed
    item_data = _get_item_data(admin_client, sample_id)
    block_data = item_data["blocks_obj"][block_id]
    block_data["freeform_comment"] = "first comment"
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200, response.json

    block_doc = database.blocks.find_one({"_id": immutable_id})
    assert block_doc["data"]["freeform_comment"] == "first comment"
    assert block_doc["version"] == 0
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 0

    # Saving the item cuts the first block version and pins it in the item snapshot
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)

    assert database.blocks.find_one({"_id": immutable_id})["version"] == 1
    versions = list(database.block_versions.find({"block_immutable_id": immutable_id}))
    assert len(versions) == 1
    assert versions[0]["version"] == 1
    assert versions[0]["data"]["freeform_comment"] == "first comment"

    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    assert item_version["data"]["blocks_obj"][block_id] == {
        "immutable_id": immutable_id,
        "version": 1,
    }

    # An unchanged save does not mint a new block or item version
    n_item_versions = database.item_versions.count_documents({"refcode": refcode})
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)
    assert database.blocks.find_one({"_id": immutable_id})["version"] == 1
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1
    assert database.item_versions.count_documents({"refcode": refcode}) == n_item_versions

    # A block content change alone produces a new item version (the changed pin
    # defeats the de-dup guard) and a new block version
    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][block_id]["freeform_comment"] = "second comment"
    _save_item(admin_client, sample_id, item_data)

    assert database.blocks.find_one({"_id": immutable_id})["version"] == 2
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 2
    assert database.item_versions.count_documents({"refcode": refcode}) == n_item_versions + 1
    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    assert item_version["data"]["blocks_obj"][block_id] == {
        "immutable_id": immutable_id,
        "version": 2,
    }

    # The manual /save-version/ endpoint also snapshots drifted block content
    item_data = _get_item_data(admin_client, sample_id)
    block_data = item_data["blocks_obj"][block_id]
    block_data["freeform_comment"] = "drifted comment"
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200

    response = admin_client.post(f"/items/{refcode}/save-version/")
    assert response.status_code == 200, response.json

    assert database.blocks.find_one({"_id": immutable_id})["version"] == 3
    latest_block_version = database.block_versions.find_one(
        {"block_immutable_id": immutable_id}, sort=[("version", -1)]
    )
    assert latest_block_version["data"]["freeform_comment"] == "drifted comment"
    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    assert item_version["data"]["blocks_obj"][block_id]["version"] == 3


def test_version_views_resolve_referenced_payloads(sample_with_block, admin_client):
    """Version previews and diffs show full block payloads, not
    `{immutable_id, version}` pins."""
    sample_id, refcode, block_id = sample_with_block

    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][block_id]["freeform_comment"] = "first comment"
    _save_item(admin_client, sample_id, item_data)

    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][block_id]["freeform_comment"] = "second comment"
    _save_item(admin_client, sample_id, item_data)

    response = admin_client.get(f"/items/{refcode}/versions/")
    assert response.status_code == 200
    versions = response.json["versions"]
    assert len(versions) >= 3  # created + two saves
    v_first = next(v for v in versions if v["version"] == 2)
    v_second = next(v for v in versions if v["version"] == 3)

    response = admin_client.get(f"/items/{refcode}/versions/{v_first['_id']}/")
    assert response.status_code == 200
    snapshot_block = response.json["version"]["data"]["blocks_obj"][block_id]
    assert snapshot_block["blocktype"] == "comment"
    assert snapshot_block["freeform_comment"] == "first comment"

    response = admin_client.get(
        f"/items/{refcode}/compare-versions/?v1={v_first['_id']}&v2={v_second['_id']}"
    )
    assert response.status_code == 200
    diff = response.json["diff"]
    changed = diff.get("values_changed", {})
    comment_key = f"root['blocks_obj']['{block_id}']['freeform_comment']"
    assert comment_key in changed
    assert changed[comment_key]["old_value"] == "first comment"
    assert changed[comment_key]["new_value"] == "second comment"


def test_restore_referenced_block(sample_with_block, admin_client, database):
    """Restore is append-only for referenced blocks: the pinned payload becomes
    the new current state plus a RESTORED history entry, and a since-deleted
    block is recreated with its original immutable_id."""
    sample_id, refcode, block_id = sample_with_block

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]

    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][block_id]["freeform_comment"] = "first comment"
    _save_item(admin_client, sample_id, item_data)

    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][block_id]["freeform_comment"] = "second comment"
    _save_item(admin_client, sample_id, item_data)

    response = admin_client.get(f"/items/{refcode}/versions/")
    v_first = next(v for v in response.json["versions"] if v["version"] == 2)

    response = admin_client.post(
        f"/items/{refcode}/restore-version/", json={"version_id": v_first["_id"]}
    )
    assert response.status_code == 200, response.json

    # The live block payload is back to the pinned content...
    block_doc = database.blocks.find_one({"_id": immutable_id})
    assert block_doc["data"]["freeform_comment"] == "first comment"
    # ...via a new RESTORED history entry (append-only)
    latest_block_version = database.block_versions.find_one(
        {"block_immutable_id": immutable_id}, sort=[("version", -1)]
    )
    assert latest_block_version["action"] == "restored"
    assert latest_block_version["version"] == block_doc["version"] == 3
    # The live item points at the block without a pin; the RESTORED item
    # snapshot pins the freshly minted block version
    stored_entry = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]
    assert stored_entry == {"immutable_id": immutable_id}
    restored_item_version = database.item_versions.find_one(
        {"refcode": refcode}, sort=[("version", -1)]
    )
    assert restored_item_version["action"] == "restored"
    assert restored_item_version["data"]["blocks_obj"][block_id] == {
        "immutable_id": immutable_id,
        "version": 3,
    }

    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][block_id]["freeform_comment"] == "first comment"

    # Delete the block, then restore again: the block document is recreated
    # with its original immutable_id from its retained history
    response = admin_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": block_id}
    )
    assert response.status_code == 200
    assert database.blocks.find_one({"_id": immutable_id}) is None
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 3

    response = admin_client.post(
        f"/items/{refcode}/restore-version/", json={"version_id": v_first["_id"]}
    )
    assert response.status_code == 200, response.json

    block_doc = database.blocks.find_one({"_id": immutable_id})
    assert block_doc is not None
    assert block_doc["data"]["freeform_comment"] == "first comment"
    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][block_id]["freeform_comment"] == "first comment"


def test_legacy_embedded_block_stays_embedded(sample_with_block, admin_client, database):
    """A legacy embedded block is frozen in embedded form across update-block,
    save-item, snapshots, and restores — no `blocks` document is ever created for
    it — while a referenced sibling in the same item works normally (mixed state)."""
    sample_id, refcode, referenced_block_id = sample_with_block

    legacy_block_id = "legacyblock12345"
    _insert_legacy_embedded_block(database, sample_id, legacy_block_id)

    # Both forms are reassembled in the API response
    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][legacy_block_id]["freeform_comment"] == "legacy comment"
    assert item_data["blocks_obj"][referenced_block_id]["blocktype"] == "comment"

    # update-block on the legacy block stays on the embedded path
    block_data = item_data["blocks_obj"][legacy_block_id]
    block_data["freeform_comment"] = "legacy edited"
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200, response.json

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert stored[legacy_block_id]["freeform_comment"] == "legacy edited"
    assert set(stored[referenced_block_id]) == {"immutable_id"}
    assert database.blocks.find_one({"block_id": legacy_block_id}) is None

    # save-item keeps each entry in its form; the snapshot embeds the legacy
    # payload verbatim and pins the referenced entry
    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][legacy_block_id]["freeform_comment"] = "legacy saved"
    _save_item(admin_client, sample_id, item_data)

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert stored[legacy_block_id]["freeform_comment"] == "legacy saved"
    assert set(stored[referenced_block_id]) == {"immutable_id"}
    assert database.blocks.find_one({"block_id": legacy_block_id}) is None

    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    snapshot_blocks = item_version["data"]["blocks_obj"]
    assert snapshot_blocks[legacy_block_id]["freeform_comment"] == "legacy saved"
    assert set(snapshot_blocks[referenced_block_id]) == {"immutable_id", "version"}
    assert item_version["data"]["display_order"] == [referenced_block_id, legacy_block_id]
    saved_version_id = str(item_version["_id"])

    # Edit again and restore the previous snapshot: the legacy block is restored
    # embedded and still has no blocks document (anti-dangling)
    item_data = _get_item_data(admin_client, sample_id)
    item_data["blocks_obj"][legacy_block_id]["freeform_comment"] = "legacy edited again"
    _save_item(admin_client, sample_id, item_data)

    response = admin_client.post(
        f"/items/{refcode}/restore-version/", json={"version_id": saved_version_id}
    )
    assert response.status_code == 200, response.json

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert stored[legacy_block_id]["freeform_comment"] == "legacy saved"
    assert set(stored[referenced_block_id]) == {"immutable_id"}
    assert database.blocks.find_one({"block_id": legacy_block_id}) is None

    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][legacy_block_id]["freeform_comment"] == "legacy saved"


def test_save_item_reconciliation(sample_with_block, admin_client, database):
    """save-item deletes the `blocks` doc of a referenced block omitted from the
    payload (retaining its history), and births unknown block IDs as references."""
    sample_id, _, block_id = sample_with_block

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]

    # Commit a version so there is history to retain
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1

    # A payload omitting the stored referenced block deletes its live document
    item_data = _get_item_data(admin_client, sample_id)
    del item_data["blocks_obj"][block_id]
    item_data["display_order"] = []
    _save_item(admin_client, sample_id, item_data)

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert block_id not in stored
    assert database.blocks.find_one({"_id": immutable_id}) is None
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1

    # A payload with an unknown block_id births a *referenced* block
    new_block_id = "clientmadeblock1"
    item_data = _get_item_data(admin_client, sample_id)
    item_data.setdefault("blocks_obj", {})[new_block_id] = {
        "blocktype": "comment",
        "block_id": new_block_id,
        "item_id": sample_id,
        "freeform_comment": "born via save-item",
    }
    item_data["display_order"] = [new_block_id]
    _save_item(admin_client, sample_id, item_data)

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert set(stored[new_block_id]) == {"immutable_id"}
    block_doc = database.blocks.find_one({"_id": stored[new_block_id]["immutable_id"]})
    assert block_doc["data"]["freeform_comment"] == "born via save-item"

    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][new_block_id]["freeform_comment"] == "born via save-item"


def test_delete_block_and_item_retain_history(sample_with_block, admin_client, database):
    """Deleting a block (or its whole item) removes the live `blocks` document(s)
    but retains `block_versions`, mirroring `item_versions`."""
    sample_id, _, block_id = sample_with_block

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]

    # Commit a version, then delete the block
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)

    response = admin_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": block_id}
    )
    assert response.status_code == 200
    assert database.blocks.find_one({"_id": immutable_id}) is None
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1
    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1, "display_order": 1})
    assert block_id not in stored["blocks_obj"]
    assert block_id not in stored["display_order"]

    # Deleting the same (now-absent) block again returns 400, on an accessible
    # item — the single-query find_one_and_update preserves this behaviour.
    response = admin_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": block_id}
    )
    assert response.status_code == 400

    # Add another block and delete the whole item
    response = admin_client.post(
        "/add-data-block/", json={"block_type": "comment", "item_id": sample_id, "index": 0}
    )
    assert response.status_code == 200
    second_block_id = response.json["new_block_obj"]["block_id"]
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)
    second_immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})[
        "blocks_obj"
    ][second_block_id]["immutable_id"]

    response = admin_client.post("/delete-sample/", json={"item_id": sample_id})
    assert response.status_code == 200
    assert database.blocks.find_one({"_id": second_immutable_id}) is None
    assert database.block_versions.count_documents({"block_immutable_id": second_immutable_id}) == 1


def test_block_created_and_deleted_before_save_leaves_no_residue(
    sample_with_block, admin_client, database
):
    """A block created and deleted before any item save has no `block_versions`
    entries to retain — nothing is left behind."""
    sample_id, _, _ = sample_with_block

    response = admin_client.post(
        "/add-data-block/", json={"block_type": "comment", "item_id": sample_id, "index": 0}
    )
    assert response.status_code == 200
    transient_block_id = response.json["new_block_obj"]["block_id"]

    transient_immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})[
        "blocks_obj"
    ][transient_block_id]["immutable_id"]

    response = admin_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": transient_block_id}
    )
    assert response.status_code == 200
    assert database.blocks.find_one({"_id": transient_immutable_id}) is None
    assert (
        database.block_versions.count_documents({"block_immutable_id": transient_immutable_id}) == 0
    )


def test_snapshot_pins_from_history_when_live_doc_missing(
    sample_with_block, admin_client, database
):
    """If a referenced block's live document is missing at snapshot time (e.g. a
    deletion race) but its history is retained, the snapshot pins the latest
    committed version instead of storing an unpinned reference."""
    sample_id, refcode, block_id = sample_with_block

    # Commit version 1 of the block
    item_data = _get_item_data(admin_client, sample_id)
    _save_item(admin_client, sample_id, item_data)

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1

    # Simulate the race: the live doc disappears while the item still references
    # it, and the item changes so the snapshot de-dup guard does not skip
    database.blocks.delete_one({"_id": immutable_id})
    database.items.update_one(
        {"item_id": sample_id}, {"$set": {"description": "changed under race"}}
    )

    response = admin_client.post(f"/items/{refcode}/save-version/")
    assert response.status_code == 200, response.json

    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    assert item_version["data"]["description"] == "changed under race"
    assert item_version["data"]["blocks_obj"][block_id] == {
        "immutable_id": immutable_id,
        "version": 1,
    }
    # No new block version was minted by the fallback
    assert database.block_versions.count_documents({"block_immutable_id": immutable_id}) == 1


def test_snapshot_drops_reference_with_no_content_anywhere(
    sample_with_block, admin_client, database
):
    """A dangling reference with no live document and no committed history is
    recorded as absent in the snapshot (never as an unresolvable reference);
    the live item document is left untouched."""
    sample_id, refcode, block_id = sample_with_block

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]

    # The block was never saved (no history); make its reference dangle and
    # change the item so the de-dup guard does not skip the snapshot
    database.blocks.delete_one({"_id": immutable_id})
    database.items.update_one({"item_id": sample_id}, {"$set": {"description": "now dangling"}})

    response = admin_client.post(f"/items/{refcode}/save-version/")
    assert response.status_code == 200, response.json

    item_version = database.item_versions.find_one({"refcode": refcode}, sort=[("version", -1)])
    assert item_version["data"]["description"] == "now dangling"
    assert block_id not in item_version["data"]["blocks_obj"]
    assert block_id not in item_version["data"]["display_order"]

    # The live item still carries the dangling reference (snapshotting must not
    # mutate the item); the read path just skips it
    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1, "display_order": 1})
    assert stored["blocks_obj"][block_id] == {"immutable_id": immutable_id}
    assert block_id in stored["display_order"]
    item_data = _get_item_data(admin_client, sample_id)
    assert block_id not in item_data["blocks_obj"]


def test_file_attachment_linkage_with_referenced_block(
    sample_with_block, admin_client, database, tmpdir
):
    """A file attached to a referenced block keeps the pre-separation linkage:
    the item lists the file, the block payload carries its `file_id`, and the
    reassembled API response reflects both."""
    sample_id, _, block_id = sample_with_block

    test_file = tmpdir.join("block_attachment.txt")
    test_file.write("file contents for block attachment")
    with open(str(test_file), "rb") as f:
        response = admin_client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": sample_id,
                "file": [(f, "block_attachment.txt")],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )
    assert response.status_code == 201, response.json
    file_id = response.json["file_id"]

    # Attach the file to the block and save it
    item_data = _get_item_data(admin_client, sample_id)
    block_data = item_data["blocks_obj"][block_id]
    block_data["file_id"] = file_id
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200, response.json

    # The file document is linked to the item, and the item lists the file
    file_doc = database.files.find_one({"_id": ObjectId(file_id)})
    assert file_doc is not None
    assert sample_id in file_doc["item_ids"]
    item_doc = database.items.find_one({"item_id": sample_id}, {"file_ObjectIds": 1})
    assert ObjectId(file_id) in item_doc["file_ObjectIds"]

    # The block's payload (in the `blocks` collection) carries the file_id
    stored_entry = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]
    block_doc = database.blocks.find_one({"_id": stored_entry["immutable_id"]})
    assert str(block_doc["data"]["file_id"]) == file_id

    # And the reassembled API response resolves the linkage
    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][block_id]["file_id"] == file_id
    assert file_id in [f["immutable_id"] for f in item_data.get("files", [])]


def test_collection_blocks_stay_embedded_and_functional(admin_client, database, random_string):
    """Collection blocks are untouched by the separation: they are stored
    embedded in the collection document, and add/update/delete still work."""
    collection_id = f"test_coll_{random_string[:8]}"
    response = admin_client.put(
        "/collections", json={"data": {"collection_id": collection_id, "title": "Block test"}}
    )
    assert response.status_code in (200, 201), response.json

    response = admin_client.post(
        "/add-collection-data-block/",
        json={"block_type": "comment", "collection_id": collection_id, "index": 0},
    )
    assert response.status_code == 200, response.json
    block_id = response.json["new_block_obj"]["block_id"]

    # Stored embedded in the collection document; no `blocks` document created
    coll_doc = database.collections.find_one({"collection_id": collection_id})
    assert coll_doc["blocks_obj"][block_id]["blocktype"] == "comment"
    assert database.blocks.find_one({"block_id": block_id}) is None

    # Updating the block goes through the (unchanged) embedded collection path
    block_data = coll_doc["blocks_obj"][block_id]
    block_data["freeform_comment"] = "collection comment"
    response = admin_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 200, response.json

    coll_doc = database.collections.find_one({"collection_id": collection_id})
    assert coll_doc["blocks_obj"][block_id]["freeform_comment"] == "collection comment"
    assert database.blocks.find_one({"block_id": block_id}) is None

    # The collection still reads fine and deletion works as before
    assert admin_client.get(f"/collections/{collection_id}").status_code == 200
    response = admin_client.post(
        "/delete-collection-block/", json={"collection_id": collection_id, "block_id": block_id}
    )
    assert response.status_code == 200, response.json
    coll_doc = database.collections.find_one({"collection_id": collection_id})
    assert block_id not in (coll_doc.get("blocks_obj") or {})


def test_no_block_content_for_user_without_item_access(
    admin_client, another_client, database, default_sample_dict, random_string
):
    """Every path that can return block or block-version content is gated by the
    parent item's permissions, and the block document's own owner fields must
    not grant access when the item denies it."""
    # The shared fixture sample carries group_ids granting the demo group read
    # access (which another_client is in), so build one without any group grant
    sample_id = f"test_block_sep_priv_{random_string[:8]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id
    sample_data.pop("group_ids", None)

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, response.json

    response = admin_client.post(
        "/add-data-block/", json={"block_type": "comment", "item_id": sample_id, "index": 0}
    )
    assert response.status_code == 200, response.json
    block_id = response.json["new_block_obj"]["block_id"]

    # Commit a version so version endpoints have content to protect
    item_data = _get_item_data(admin_client, sample_id)
    refcode = item_data["refcode"]
    _save_item(admin_client, sample_id, item_data)
    version_id = admin_client.get(f"/items/{refcode}/versions/").json["versions"][0]["_id"]

    def assert_no_access():
        assert another_client.get(f"/get-item-data/{sample_id}").status_code == 404
        assert another_client.get(f"/item-graph/{sample_id}").status_code == 404
        assert another_client.get(f"/items/{refcode}/versions/").status_code == 404
        assert another_client.get(f"/items/{refcode}/versions/{version_id}/").status_code == 404
        assert (
            another_client.post(
                f"/items/{refcode}/restore-version/", json={"version_id": version_id}
            ).status_code
            == 404
        )
        samples = another_client.get("/samples/").json["samples"]
        assert sample_id not in [s["item_id"] for s in samples]

    assert_no_access()

    # Even if the *block document* names the other user as creator/group member,
    # access is still denied: the parent item is the sole access authority
    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]
    another_user_id = ObjectId(24 * "7")  # `another_client`'s user, per conftest
    database.blocks.update_one(
        {"_id": immutable_id},
        {"$set": {"creator_ids": [another_user_id], "group_ids": [another_user_id]}},
    )
    assert_no_access()

    admin_client.post("/delete-sample/", json={"item_id": sample_id})


def test_item_created_with_client_blocks_obj_stays_embedded(
    admin_client, default_sample_dict, database, random_string
):
    """An API client can still supply `blocks_obj` at item creation; such blocks
    are stored embedded (legacy form) and live on the embedded path."""
    sample_id = f"test_block_sep_create_{random_string[:8]}"
    embedded_block_id = "clientcreated123"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id
    sample_data["blocks_obj"] = {
        embedded_block_id: {
            "blocktype": "comment",
            "block_id": embedded_block_id,
            "item_id": sample_id,
            "freeform_comment": "born embedded at creation",
        }
    }
    sample_data["display_order"] = [embedded_block_id]

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, response.json

    stored = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"]
    assert stored[embedded_block_id]["freeform_comment"] == "born embedded at creation"
    assert database.blocks.find_one({"block_id": embedded_block_id}) is None

    item_data = _get_item_data(admin_client, sample_id)
    assert item_data["blocks_obj"][embedded_block_id]["blocktype"] == "comment"

    admin_client.post("/delete-sample/", json={"item_id": sample_id})


def test_block_write_permissions(sample_with_block, admin_client, another_client, database):
    """Block writes are authorized via the parent item: another user cannot
    update or delete a block on an item they cannot access, and a missing
    item_id is rejected."""
    sample_id, _, block_id = sample_with_block

    item_data = _get_item_data(admin_client, sample_id)
    block_data = item_data["blocks_obj"][block_id]
    original_comment = block_data.get("freeform_comment")
    block_data["freeform_comment"] = "sneaky edit"

    # Another (non-admin) user gets a 404 and the block is unchanged
    response = another_client.post("/update-block/", json={"block_data": block_data})
    assert response.status_code == 404

    immutable_id = database.items.find_one({"item_id": sample_id}, {"blocks_obj": 1})["blocks_obj"][
        block_id
    ]["immutable_id"]
    block_doc = database.blocks.find_one({"_id": immutable_id})
    assert block_doc["data"].get("freeform_comment") == original_comment

    # A request without an item_id is a 400
    no_item_block_data = {k: v for k, v in block_data.items() if k != "item_id"}
    response = admin_client.post("/update-block/", json={"block_data": no_item_block_data})
    assert response.status_code == 400

    # Another user cannot delete the block either
    response = another_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": block_id}
    )
    assert response.status_code == 400
    assert database.blocks.find_one({"_id": immutable_id}) is not None
