"""Tests for the scoped tags routes.

Tags have scopes:

- **global**: available to (and usable by) everyone; only administrators can
  create, edit or delete them.
- **user**: a user-defined tag owned by exactly one user; only that user can list,
  use, edit or delete it (though it is still *displayed* on any item the viewer
  can access).

Names are unique *within a scope*; the stable identity of a tag is its
`immutable_id`.
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


def _create_tag(client, name, scope=None, description=None, color=None):
    """Helper to PUT a tag and return the response."""
    data = {"name": name}
    if scope is not None:
        data["scope"] = scope
    if description is not None:
        data["description"] = description
    if color is not None:
        data["color"] = color
    return client.put("/tags", json={"data": data})


# --- creation & authoring policy -------------------------------------------------


def test_create_user_defined_tag(client, unauthenticated_client, user_id):
    """Any logged-in user can create a user-defined tag they own; the default scope is
    ``user``. (Previously tag creation was admin-only; users can now self-serve.)"""
    # An unauthenticated user is rejected.
    assert _create_tag(unauthenticated_client, "unauth-tag").status_code == 401

    # A normal user can create a user-defined tag (scope defaults to "user").
    response = _create_tag(client, "my-tag", description="mine", color="#f1c40f")
    assert response.status_code == 201, response.json
    tag = response.json["data"]
    assert tag["type"] == "tags"
    assert tag["name"] == "my-tag"
    assert tag["color"] == "#f1c40f"
    assert tag["scope"] == "user"
    assert tag["owner"] == str(user_id)
    assert tag["immutable_id"]

    # Scope is modelled without the HasOwner mixin.
    assert "creator_ids" not in tag
    assert "group_ids" not in tag


def test_create_global_tag_admin_only(client, admin_client):
    """Only an administrator can create a global tag."""
    # A normal user cannot create a global tag.
    assert _create_tag(client, "user-global", scope="global").status_code == 403

    # An admin can; it has no owner.
    response = _create_tag(admin_client, "admin-global", scope="global")
    assert response.status_code == 201, response.json
    tag = response.json["data"]
    assert tag["scope"] == "global"
    assert tag["owner"] is None


def test_invalid_scope_rejected(client):
    """An unknown scope value is a 400."""
    assert _create_tag(client, "weird", scope="team").status_code == 400


# --- visibility ------------------------------------------------------------------


def test_user_defined_tag_visibility(client, another_client, admin_client, user_id):
    """A user-defined tag is listed/searchable only by its owner."""
    tag_id = _create_tag(client, "secret-tag", color="#abcdef").json["data"]["immutable_id"]

    # The owner sees it in the listing and search, marked as a user-scoped tag.
    listed = {t["name"]: t for t in client.get("/tags").json["data"]}
    assert "secret-tag" in listed
    assert listed["secret-tag"]["scope"] == "user"
    assert listed["secret-tag"]["owner"] == str(user_id)

    found = {
        r["name"]: r
        for r in client.get("/search-tags", query_string={"query": "secret"}).json["data"]
    }
    assert found["secret-tag"]["scope"] == "user"

    # Another user (and an admin, without sudo) does not see it at all.
    for other in (another_client, admin_client):
        names = {t["name"] for t in other.get("/tags").json["data"]}
        assert "secret-tag" not in names
        search = other.get("/search-tags", query_string={"query": "secret"}).json["data"]
        assert all(r["immutable_id"] != tag_id for r in search)


def test_global_tag_visible_to_all(client, another_client, admin_client):
    """A global tag is listed and searchable by everyone, with scope ``global``."""
    assert (
        _create_tag(admin_client, "shared-tag", scope="global", color="#abcdef").status_code == 201
    )

    for c in (client, another_client, admin_client):
        listed = {t["name"]: t for t in c.get("/tags").json["data"]}
        assert "shared-tag" in listed
        assert listed["shared-tag"]["scope"] == "global"

        found = {
            r["name"]: r
            for r in c.get("/search-tags", query_string={"query": "shared"}).json["data"]
        }
        assert found["shared-tag"]["scope"] == "global"
        assert found["shared-tag"]["type"] == "tags"

    # The empty-query case is still rejected.
    assert client.get("/search-tags", query_string={"query": ""}).status_code == 400


# --- scope-based name uniqueness -------------------------------------------------


def test_scope_based_name_uniqueness(client, another_client, admin_client):
    """Names are unique within a scope, but may repeat across scopes/owners."""
    # A global and a user-defined tag may share a name.
    assert _create_tag(admin_client, "flammable", scope="global").status_code == 201
    assert _create_tag(client, "flammable").status_code == 201

    # Two different users may each own a user-defined "flammable".
    assert _create_tag(another_client, "flammable").status_code == 201

    # The same owner cannot create a second user-defined tag with the same name.
    assert _create_tag(client, "flammable").status_code == 409

    # A second global with the same name is rejected.
    assert _create_tag(admin_client, "flammable", scope="global").status_code == 409


# --- editing & deletion ----------------------------------------------------------


def test_patch_tag_owner_only(client, another_client, admin_client):
    """User-defined tags are editable only by their owner; global tags only by admins."""
    user_defined_id = _create_tag(client, "editable", description="first").json["data"][
        "immutable_id"
    ]
    global_id = _create_tag(admin_client, "global-editable", scope="global").json["data"][
        "immutable_id"
    ]

    # Another user cannot edit someone else's user-defined tag.
    assert (
        another_client.patch(
            f"/tags/{user_defined_id}", json={"data": {"description": "nope"}}
        ).status_code
        == 403
    )

    # The owner can.
    assert (
        client.patch(
            f"/tags/{user_defined_id}", json={"data": {"description": "updated"}}
        ).status_code
        == 200
    )
    patched = next(
        t for t in client.get("/tags").json["data"] if t["immutable_id"] == user_defined_id
    )
    assert patched["description"] == "updated"

    # A non-admin cannot edit a global tag; an admin can.
    assert (
        client.patch(f"/tags/{global_id}", json={"data": {"description": "x"}}).status_code == 403
    )
    assert (
        admin_client.patch(f"/tags/{global_id}", json={"data": {"description": "y"}}).status_code
        == 200
    )

    # Scope/owner are immutable through PATCH.
    assert (
        client.patch(f"/tags/{user_defined_id}", json={"data": {"scope": "global"}}).status_code
        == 200
    )
    still = next(
        t for t in client.get("/tags").json["data"] if t["immutable_id"] == user_defined_id
    )
    assert still["scope"] == "user"

    # An invalid ID is a 400; a missing tag is a 404.
    assert client.patch("/tags/not-an-object-id", json={"data": {"name": "x"}}).status_code == 400
    assert client.patch(f"/tags/{ObjectId()}", json={"data": {"name": "x"}}).status_code == 404


def test_patch_tag_rename_unique_within_scope(client):
    """Renaming a user-defined tag onto another of the owner's names is rejected."""
    tag_id = _create_tag(client, "one").json["data"]["immutable_id"]
    assert _create_tag(client, "two").status_code == 201

    assert client.patch(f"/tags/{tag_id}", json={"data": {"name": "two"}}).status_code == 409


def test_delete_tag_owner_only(client, another_client, admin_client, database):
    """User-defined tags are deletable only by their owner; global only by admins; refs
    are pulled from items on delete."""
    user_defined_id = _create_tag(client, "deletable", color="#abcdef").json["data"]["immutable_id"]

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
                "data": {"tags": [{"type": "tags", "immutable_id": user_defined_id}]},
            },
        ).status_code
        == 200
    )

    # Another user cannot delete someone else's user-defined tag.
    assert another_client.delete(f"/tags/{user_defined_id}").status_code == 403

    # An admin cannot delete another user's user-defined tag either (admins manage global).
    assert admin_client.delete(f"/tags/{user_defined_id}").status_code == 403

    # The owner can.
    assert client.delete(f"/tags/{user_defined_id}").status_code == 200
    names = {t["name"] for t in client.get("/tags").json["data"]}
    assert "deletable" not in names

    # The reference is pulled from the item document in the database.
    stored = database.items.find_one({"item_id": "tag-delete"})
    assert [t for t in stored.get("tags", []) if isinstance(t, dict)] == []

    # Deleting a non-existent tag is a 404.
    assert client.delete(f"/tags/{user_defined_id}").status_code == 404

    # Global tags: only admins can delete.
    global_id = _create_tag(admin_client, "global-del", scope="global").json["data"]["immutable_id"]
    assert client.delete(f"/tags/{global_id}").status_code == 403
    assert admin_client.delete(f"/tags/{global_id}").status_code == 200


# --- applying tags to items (add-authorization) ----------------------------------


def _make_shared_sample(client, database, item_id, extra_owner_id):
    """Create a sample via the API, then share write access with a second user by
    adding them to `creator_ids` directly (mirrors co-ownership)."""
    assert (
        client.post("/new-sample/", json={"type": "samples", "item_id": item_id}).status_code == 201
    )
    database.items.update_one({"item_id": item_id}, {"$addToSet": {"creator_ids": extra_owner_id}})


def _item_tag_ids(client, item_id):
    resp = client.get(f"/get-item-data/{item_id}")
    assert resp.status_code == 200, resp.json
    return [t["immutable_id"] for t in resp.json["item_data"]["tags"] if isinstance(t, dict)]


def test_cannot_add_others_user_defined_tag(
    client, another_client, admin_client, database, another_user_id
):
    """A user may add global and own user-defined tags, but not another user's
    user-defined tag; they may keep and remove an already-present foreign tag."""
    a_tag = _create_tag(client, "a-user-defined").json["data"]["immutable_id"]
    b_tag = _create_tag(another_client, "b-user-defined").json["data"]["immutable_id"]
    g_tag = _create_tag(admin_client, "g-global", scope="global").json["data"]["immutable_id"]

    # A shared sample both users can write.
    _make_shared_sample(client, database, "shared-item", another_user_id)

    def save(c, tags):
        return c.post(
            "/save-item/",
            json={"item_id": "shared-item", "data": {"tags": tags}},
        )

    def ref(tid):
        return {"type": "tags", "immutable_id": tid}

    # B can add a global tag and their own user-defined tag.
    assert save(another_client, [ref(g_tag), ref(b_tag)]).status_code == 200
    assert set(_item_tag_ids(another_client, "shared-item")) == {g_tag, b_tag}

    # B cannot *introduce* A's user-defined tag (a new addition B does not own).
    assert save(another_client, [ref(g_tag), ref(b_tag), ref(a_tag)]).status_code == 403
    # The rejected save left the stored tags unchanged.
    assert set(_item_tag_ids(another_client, "shared-item")) == {g_tag, b_tag}

    # A (the owner) can add their own user-defined tag; the item now carries it.
    assert save(client, [ref(g_tag), ref(b_tag), ref(a_tag)]).status_code == 200
    assert set(_item_tag_ids(client, "shared-item")) == {g_tag, b_tag, a_tag}

    # B may *keep* A's already-present tag through an unrelated re-save (no new
    # foreign tag is introduced), and may *remove* it (removal is never blocked).
    assert save(another_client, [ref(g_tag), ref(b_tag), ref(a_tag)]).status_code == 200
    assert save(another_client, [ref(g_tag), ref(b_tag)]).status_code == 200
    assert set(_item_tag_ids(another_client, "shared-item")) == {g_tag, b_tag}


def test_cannot_add_foreign_tag_on_creation(client, another_client):
    """User-defined tags owned by another user are rejected at item creation too."""
    b_tag = _create_tag(another_client, "b-only").json["data"]["immutable_id"]

    response = client.post(
        "/new-sample/",
        json={
            "type": "samples",
            "item_id": "create-foreign",
            "tags": [{"type": "tags", "immutable_id": b_tag}],
        },
    )
    assert response.status_code == 403, response.json


# --- read-time resolution --------------------------------------------------------


def test_item_tag_resolution_includes_scope(
    client, another_client, admin_client, database, another_user_id
):
    """Resolved item tags carry `scope`, and another user viewing a shared item
    sees the owner's user-defined tag (display is gated by the item, not the tag)."""
    user_defined_id = _create_tag(client, "resolve-user-defined", color="#abcdef").json["data"][
        "immutable_id"
    ]
    global_id = _create_tag(admin_client, "resolve-global", scope="global").json["data"][
        "immutable_id"
    ]

    _make_shared_sample(client, database, "resolve-item", another_user_id)

    save = client.post(
        "/save-item/",
        json={
            "item_id": "resolve-item",
            "data": {
                "tags": [
                    {"type": "tags", "immutable_id": user_defined_id, "name": "stale"},
                    {"type": "tags", "immutable_id": global_id},
                ]
            },
        },
    )
    assert save.status_code == 200, save.json

    # Stored references are minimal (no display fields, incl. scope).
    stored = database.items.find_one({"item_id": "resolve-item"})
    assert {(t["type"], t["immutable_id"]) for t in stored["tags"]} == {
        ("tags", ObjectId(user_defined_id)),
        ("tags", ObjectId(global_id)),
    }

    # Another user viewing the shared item sees both tags, with resolved scope.
    tags = {
        t["immutable_id"]: t
        for t in another_client.get("/get-item-data/resolve-item").json["item_data"]["tags"]
        if isinstance(t, dict)
    }
    assert tags[user_defined_id]["scope"] == "user"
    assert tags[user_defined_id]["name"] == "resolve-user-defined"  # re-resolved, not stale
    assert tags[user_defined_id]["color"] == "#abcdef"
    assert tags[global_id]["scope"] == "global"


# --- feature flag ----------------------------------------------------------------


def test_tags_feature_flag_gate(client, admin_client, monkeypatch):
    """When the `tags` feature flag is off, the whole blueprint 404s."""
    from pydatalab.feature_flags import FEATURE_FLAGS

    monkeypatch.setattr(FEATURE_FLAGS, "tags", False)
    assert client.get("/tags").status_code == 404
    assert client.get("/search-tags", query_string={"query": "x"}).status_code == 404
    assert _create_tag(client, "flagged-off").status_code == 404


def test_tags_stripped_on_creation(client, admin_client, database):
    """Tags provided directly at item creation are stored as minimal references."""
    tag_id = _create_tag(admin_client, "create-global", scope="global", color="#abcdef").json[
        "data"
    ]["immutable_id"]

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
