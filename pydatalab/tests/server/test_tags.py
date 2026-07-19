"""Tests for the (simplified) tags routes.

Tags are global: only administrators can create/edit/delete them, but every user
can list, search and apply them. There is no ownership/scope in this stage.
"""

import pytest
from bson import ObjectId


@pytest.fixture(autouse=True)
def _isolate_tags(database):
    """Isolate each test.

    The test database is only dropped per-module, so the `tags` collection would
    otherwise leak between tests. Clear it before and after each test.
    """
    database.tags.delete_many({})
    yield
    database.tags.delete_many({})


def _create_tag(client, name, description=None, color=None):
    """Helper to PUT a tag and return the response."""
    data = {"name": name}
    if description is not None:
        data["description"] = description
    if color is not None:
        data["color"] = color
    return client.put("/tags", json={"data": data})


def test_create_tag_requires_admin(client, admin_client, unauthenticated_client):
    """Only an administrator can create a tag."""
    # An unauthenticated user is rejected.
    assert _create_tag(unauthenticated_client, "unauth-tag").status_code == 401

    # An authenticated non-admin user is forbidden.
    assert _create_tag(client, "user-tag").status_code == 403

    # An admin can create the tag.
    response = _create_tag(admin_client, "admin-tag", "An example", color="#f1c40f")
    assert response.status_code == 201, response.json
    tag = response.json["data"]
    assert tag["type"] == "tags"
    assert tag["name"] == "admin-tag"
    assert tag["color"] == "#f1c40f"
    assert tag["immutable_id"]
    # Tags carry no ownership/scope in this stage.
    assert "creator_ids" not in tag
    assert "group_ids" not in tag


def test_duplicate_tag_rejected(admin_client):
    """Tag names are globally unique."""
    assert _create_tag(admin_client, "duplicate-tag").status_code == 201
    assert _create_tag(admin_client, "duplicate-tag").status_code == 409


def test_list_and_search_tags(client, another_client, admin_client):
    """All users can list and search all tags; results carry no scope/ownership."""
    assert _create_tag(admin_client, "searchable-one", color="#abcdef").status_code == 201
    assert _create_tag(admin_client, "searchable-two", "a description").status_code == 201

    # Any user sees every tag in the listing.
    for c in (client, another_client, admin_client):
        response = c.get("/tags")
        assert response.status_code == 200, response.json
        names = {t["name"] for t in response.json["data"]}
        assert {"searchable-one", "searchable-two"} <= names

    # Full-text search returns reference-shaped results with name/description/color.
    response = client.get("/search-tags", query_string={"query": "searchable"})
    assert response.status_code == 200, response.json
    results = {r["name"]: r for r in response.json["data"]}
    assert {"searchable-one", "searchable-two"} <= set(results)
    for result in response.json["data"]:
        assert result["type"] == "tags"
        assert result["immutable_id"]
    assert results["searchable-one"]["color"] == "#abcdef"
    assert results["searchable-two"]["description"] == "a description"

    # The empty-query case is rejected.
    assert client.get("/search-tags", query_string={"query": ""}).status_code == 400


def test_patch_tag(client, admin_client):
    """An admin can rename/re-describe a tag; non-admins cannot; names stay unique."""
    tag_id = _create_tag(admin_client, "patchable", "first").json["data"]["immutable_id"]
    assert _create_tag(admin_client, "patchable-other").status_code == 201

    # A non-admin cannot edit a tag.
    assert (
        client.patch(f"/tags/{tag_id}", json={"data": {"description": "nope"}}).status_code == 403
    )

    # An admin can.
    response = admin_client.patch(f"/tags/{tag_id}", json={"data": {"description": "updated"}})
    assert response.status_code == 200, response.json

    patched = next(t for t in client.get("/tags").json["data"] if t["immutable_id"] == tag_id)
    assert patched["description"] == "updated"

    # Renaming onto an existing name is rejected.
    response = admin_client.patch(f"/tags/{tag_id}", json={"data": {"name": "patchable-other"}})
    assert response.status_code == 409, response.json

    # An invalid ID is a 400.
    assert (
        admin_client.patch("/tags/not-an-object-id", json={"data": {"name": "x"}}).status_code
        == 400
    )


def test_delete_tag(client, admin_client, database):
    """Only an admin can delete a tag; its references are pulled from items."""
    tag_id = _create_tag(admin_client, "deletable", color="#abcdef").json["data"]["immutable_id"]

    # Apply the tag to an item to check the reference cleanup on delete.
    assert (
        client.post("/new-sample/", json={"type": "samples", "item_id": "tag-delete"}).status_code
        == 201
    )
    assert (
        client.post(
            "/save-item/",
            json={
                "item_id": "tag-delete",
                "data": {"tags": [{"type": "tags", "immutable_id": tag_id}]},
            },
        ).status_code
        == 200
    )

    # A non-admin cannot delete the tag.
    assert client.delete(f"/tags/{tag_id}").status_code == 403

    # An admin can.
    assert admin_client.delete(f"/tags/{tag_id}").status_code == 200

    names = {t["name"] for t in client.get("/tags").json["data"]}
    assert "deletable" not in names

    # The reference is pulled from the item document in the database.
    stored = database.items.find_one({"item_id": "tag-delete"})
    assert [t for t in stored.get("tags", []) if isinstance(t, dict)] == []

    # Deleting a non-existent tag is a 404.
    assert admin_client.delete(f"/tags/{tag_id}").status_code == 404


def test_tags_feature_flag_gate(client, admin_client, monkeypatch):
    """When the `tags` feature flag is off, the whole blueprint 404s."""
    from pydatalab.feature_flags import FEATURE_FLAGS

    monkeypatch.setattr(FEATURE_FLAGS, "tags", False)
    assert client.get("/tags").status_code == 404
    assert client.get("/search-tags", query_string={"query": "x"}).status_code == 404
    assert _create_tag(admin_client, "flagged-off").status_code == 404


def test_item_tag_resolution(client, admin_client, database):
    """Tag references on an item are resolved (and refreshed) on read; deleted tags drop out.

    Also covers the route-level round-trip of the `tags` field (references).
    """
    # A global tag (with a color) that the normal user can apply.
    tag_id = _create_tag(admin_client, "test-resolve-tag", color="#abcdef").json["data"][
        "immutable_id"
    ]

    # Apply it to a sample, with a deliberately stale inlined name.
    assert (
        client.post("/new-sample/", json={"type": "samples", "item_id": "tag-resolve"}).status_code
        == 201
    )
    save = client.post(
        "/save-item/",
        json={
            "item_id": "tag-resolve",
            "data": {
                "tags": [
                    {"type": "tags", "immutable_id": tag_id, "name": "stale name"},
                ]
            },
        },
    )
    assert save.status_code == 200, save.json

    # The stored item keeps only the minimal `{type, immutable_id}` reference —
    # display fields (name/description/color) are not persisted.
    stored = database.items.find_one({"item_id": "tag-resolve"})
    assert stored["tags"] == [{"type": "tags", "immutable_id": ObjectId(tag_id)}]

    def _get_tags():
        resp = client.get("/get-item-data/tag-resolve")
        assert resp.status_code == 200, resp.json
        return resp.json["item_data"]["tags"]

    tags = _get_tags()
    refs = [t for t in tags if isinstance(t, dict)]
    # The reference resolves to the *current* name, not the stale stored one.
    assert len(refs) == 1
    assert refs[0]["immutable_id"] == tag_id
    assert refs[0]["name"] == "test-resolve-tag"
    # The tag's color is inlined on the resolved reference.
    assert refs[0]["color"] == "#abcdef"

    # Renaming the tag is reflected on the next read.
    assert (
        admin_client.patch(
            f"/tags/{tag_id}", json={"data": {"name": "test-resolve-renamed"}}
        ).status_code
        == 200
    )
    refs = [t for t in _get_tags() if isinstance(t, dict)]
    assert refs[0]["name"] == "test-resolve-renamed"

    # A dangling reference (e.g. one surviving in a restored version) is dropped on read.
    database.items.update_one(
        {"item_id": "tag-resolve"},
        {"$push": {"tags": {"type": "tags", "immutable_id": ObjectId()}}},
    )
    refs = [t for t in _get_tags() if isinstance(t, dict)]
    assert len(refs) == 1
    assert refs[0]["immutable_id"] == tag_id

    # Deleting the tag removes the reference.
    assert admin_client.delete(f"/tags/{tag_id}").status_code == 200
    assert _get_tags() == []


def test_tags_stripped_on_creation(client, admin_client, database):
    """Tags provided directly at item creation are stored as minimal references too."""
    tag_id = _create_tag(admin_client, "test-create-tag", color="#abcdef").json["data"][
        "immutable_id"
    ]

    response = client.post(
        "/new-sample/",
        json={
            "type": "samples",
            "item_id": "tag-on-create",
            "tags": [
                {"type": "tags", "immutable_id": tag_id, "name": "stale", "color": "#abcdef"},
            ],
        },
    )
    assert response.status_code == 201, response.json

    stored = database.items.find_one({"item_id": "tag-on-create"})
    assert stored["tags"] == [{"type": "tags", "immutable_id": ObjectId(tag_id)}]
