"""Tests for the scoped tags routes.

Tags have scopes:

- **global**: available to (and usable by) everyone; only administrators can
  create, edit or delete them.
- **user**: a user-defined tag owned by exactly one user; only that user can use it,
  and only that user and administrators (in super-user mode for listing) can list,
  edit or delete it (though it is still *displayed* on any item the viewer can
  access).
- **group**: a tag owned by exactly one group (its ID is stored as `owner`); members
  of the group can list and use it, while the group's managers and administrators
  can create, edit and delete it (it is also *displayed* on any item the viewer can
  access).

Names are unique *within a scope*; the stable identity of a tag is its
`immutable_id`.
"""

import pytest
from bson import ObjectId


@pytest.fixture(autouse=True)
def _isolate_tags(database):
    """Isolate each test.

    The test database is only dropped per-module, so the `tags` collection (and the
    group managers set by the group-tag tests) would otherwise leak between tests.
    Reset them before and after each test.
    """
    database.tags.delete_many({})
    database.groups.update_many({}, {"$unset": {"managers": ""}})
    yield
    database.tags.delete_many({})
    database.groups.update_many({}, {"$unset": {"managers": ""}})


OTHER_GROUP_ID = ObjectId(24 * "9")


@pytest.fixture
def other_group(database, another_user_id):
    """A second group whose only member is `another_user` (and with no managers).

    `user` (the `client` fixture) is a member of the demo group only, so it is a
    non-member of this group; the admin is a member of neither.
    """
    database.groups.insert_one(
        {"_id": OTHER_GROUP_ID, "display_name": "Other Group", "group_id": "other-tags"}
    )
    database.users.update_one(
        {"_id": another_user_id}, {"$push": {"groups": {"immutable_id": OTHER_GROUP_ID}}}
    )
    yield OTHER_GROUP_ID
    database.users.update_one(
        {"_id": another_user_id}, {"$pull": {"groups": {"immutable_id": OTHER_GROUP_ID}}}
    )
    database.groups.delete_one({"_id": OTHER_GROUP_ID})


def _set_group_managers(database, group_id, managers):
    """Make the given users the managers of the given group (mirrors the admin route)."""
    database.groups.update_one({"_id": group_id}, {"$set": {"managers": managers}})


def _create_tag(client, name, scope=None, description=None, color=None, owner=None):
    """Helper to PUT a tag and return the response."""
    data = {"name": name}
    if scope is not None:
        data["scope"] = scope
    if owner is not None:
        data["owner"] = str(owner)
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

    # Only administrators can change the scope through PATCH. (Non-admins' scope changes
    # used to be silently ignored with a 200; they are now rejected, since administrators
    # can change the scope through this endpoint.)
    assert (
        client.patch(f"/tags/{user_defined_id}", json={"data": {"scope": "global"}}).status_code
        == 403
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
    """User-defined tags are deletable only by their owner (and administrators); global
    only by admins; refs are pulled from items on delete."""
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

    # An admin can delete another user's user-defined tag. (This used to be a 403, before
    # administrators could manage every tag.) Check it on a separate tag, so that the
    # owner's deletion and reference cleanup below are still exercised.
    admin_deletable_id = _create_tag(client, "admin-deletable").json["data"]["immutable_id"]
    assert admin_client.delete(f"/tags/{admin_deletable_id}").status_code == 200

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


# --- group tags ------------------------------------------------------------------


def test_create_group_tag_authorization(
    client, another_client, admin_client, database, user_id, group_id, other_group
):
    """Group tags can be created by administrators and by the group's managers only."""
    # A plain member of the demo group (not a manager) cannot create a tag for it.
    assert _create_tag(client, "team", scope="group", owner=group_id).status_code == 403

    # Once a manager of the demo group, they can.
    _set_group_managers(database, group_id, [user_id])
    response = _create_tag(client, "team", scope="group", owner=group_id, color="#123456")
    assert response.status_code == 201, response.json
    tag = response.json["data"]
    assert tag["scope"] == "group"
    assert tag["owner"] == str(group_id)
    assert tag["owner_name"] == "Demo Group"
    assert tag["can_manage"] is True

    # Managing the demo group does not allow creating tags for another group.
    assert _create_tag(client, "team", scope="group", owner=other_group).status_code == 403

    # An administrator can create a tag for any group, without being a member.
    response = _create_tag(admin_client, "admin-team", scope="group", owner=other_group)
    assert response.status_code == 201, response.json
    assert response.json["data"]["owner"] == str(other_group)

    # The owning group is required and must exist.
    assert _create_tag(admin_client, "no-group", scope="group").status_code == 400
    assert _create_tag(admin_client, "bad-group", scope="group", owner="nope").status_code == 400
    assert (
        _create_tag(admin_client, "missing-group", scope="group", owner=ObjectId()).status_code
        == 400
    )


def test_group_tag_visibility(
    client, another_client, admin_client, database, user_id, group_id, other_group
):
    """Group tags are listed and searchable by the group's members. Managers and
    administrators that are not members see them in the listing (to manage them) but
    not in the search used to add tags to items."""
    tag_id = _create_tag(admin_client, "other-team", scope="group", owner=other_group).json["data"][
        "immutable_id"
    ]

    def listed(c):
        return {t["immutable_id"]: t for t in c.get("/tags").json["data"]}

    def searched(c):
        response = c.get("/search-tags", query_string={"query": "other-team"})
        assert response.status_code == 200, response.json
        return {r["immutable_id"]: r for r in response.json["data"]}

    # A member (another_user) lists and finds it, but cannot manage it.
    member_listing = listed(another_client)
    assert member_listing[tag_id]["scope"] == "group"
    assert member_listing[tag_id]["owner_name"] == "Other Group"
    assert member_listing[tag_id]["can_manage"] is False
    member_search = searched(another_client)
    assert member_search[tag_id]["scope"] == "group"
    assert member_search[tag_id]["owner_name"] == "Other Group"

    # A non-member (user) neither lists nor finds it.
    assert tag_id not in listed(client)
    assert tag_id not in searched(client)

    # A non-member administrator lists it (and can manage it), but cannot find it.
    admin_listing = listed(admin_client)
    assert admin_listing[tag_id]["can_manage"] is True
    assert tag_id not in searched(admin_client)

    # A non-member manager of the group lists it (and can manage it), but cannot find it.
    _set_group_managers(database, other_group, [user_id])
    manager_listing = listed(client)
    assert manager_listing[tag_id]["can_manage"] is True
    assert tag_id not in searched(client)


def test_listing_can_manage_flag(client, another_client, admin_client):
    """The `can_manage` flag reflects the edit/delete rules for user and global tags."""
    user_tag = _create_tag(client, "flag-user").json["data"]["immutable_id"]
    global_tag = _create_tag(admin_client, "flag-global", scope="global").json["data"][
        "immutable_id"
    ]

    owner_listing = {t["immutable_id"]: t for t in client.get("/tags").json["data"]}
    assert owner_listing[user_tag]["can_manage"] is True
    assert owner_listing[global_tag]["can_manage"] is False

    admin_listing = {t["immutable_id"]: t for t in admin_client.get("/tags").json["data"]}
    assert admin_listing[global_tag]["can_manage"] is True

    # User tags carry their owner's display name; global tags have no owner name.
    assert owner_listing[user_tag]["owner_name"] == "Test User"
    assert "owner_name" not in owner_listing[global_tag]


def test_group_tag_names_unique_per_group(client, admin_client, group_id, other_group):
    """Group tag names are unique within a group, but may repeat across groups and
    scopes."""
    assert _create_tag(admin_client, "team", scope="group", owner=group_id).status_code == 201
    assert _create_tag(admin_client, "team", scope="group", owner=group_id).status_code == 409
    assert _create_tag(admin_client, "team", scope="group", owner=other_group).status_code == 201
    assert _create_tag(admin_client, "team", scope="global").status_code == 201
    assert _create_tag(client, "team").status_code == 201

    # Renaming onto an existing name in the same group conflicts.
    other_id = _create_tag(admin_client, "team-2", scope="group", owner=group_id).json["data"][
        "immutable_id"
    ]
    assert (
        admin_client.patch(f"/tags/{other_id}", json={"data": {"name": "team"}}).status_code == 409
    )


def test_group_tag_edit_delete_by_managers_and_admins(
    client, another_client, admin_client, database, user_id, group_id
):
    """Group tags can be edited and deleted by the group's managers and by
    administrators, not by plain members."""
    tag_id = _create_tag(admin_client, "managed", scope="group", owner=group_id).json["data"][
        "immutable_id"
    ]

    def patch(c, description):
        return c.patch(f"/tags/{tag_id}", json={"data": {"description": description}})

    # Plain members cannot edit or delete it.
    assert patch(client, "nope").status_code == 403
    assert client.delete(f"/tags/{tag_id}").status_code == 403

    # A manager can edit it, but not change its scope (administrators only; this used
    # to be silently ignored rather than rejected).
    _set_group_managers(database, group_id, [user_id])
    response = client.patch(
        f"/tags/{tag_id}",
        json={"data": {"description": "by manager", "scope": "global", "owner": None}},
    )
    assert response.status_code == 403, response.json
    response = client.patch(f"/tags/{tag_id}", json={"data": {"description": "by manager"}})
    assert response.status_code == 200, response.json
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert stored["description"] == "by manager"
    assert stored["scope"] == "group"
    assert stored["owner"] == group_id

    # Another member that is not a manager still cannot delete it.
    assert another_client.delete(f"/tags/{tag_id}").status_code == 403

    # An administrator can edit it.
    assert patch(admin_client, "by admin").status_code == 200

    # The manager can delete it.
    assert client.delete(f"/tags/{tag_id}").status_code == 200
    assert database.tags.find_one({"_id": ObjectId(tag_id)}) is None

    # An administrator can delete group tags too.
    second_id = _create_tag(admin_client, "managed-2", scope="group", owner=group_id).json["data"][
        "immutable_id"
    ]
    assert admin_client.delete(f"/tags/{second_id}").status_code == 200


def test_manageable_groups(
    client, another_client, admin_client, database, user_id, group_id, other_group
):
    """`/tags/manageable-groups` lists the groups the caller may create group tags for."""

    def manageable(c):
        response = c.get("/tags/manageable-groups")
        assert response.status_code == 200, response.json
        return {g["immutable_id"]: g for g in response.json["data"]}

    # Plain members manage no groups.
    assert manageable(client) == {}
    assert manageable(another_client) == {}

    # A manager gets the groups they manage, whether or not they are a member.
    _set_group_managers(database, group_id, [user_id])
    _set_group_managers(database, other_group, [user_id])
    groups = manageable(client)
    assert set(groups) == {str(group_id), str(other_group)}
    assert groups[str(group_id)]["display_name"] == "Demo Group"
    assert groups[str(group_id)]["group_id"] == "demo"
    assert manageable(another_client) == {}

    # Administrators get all groups.
    assert {str(group_id), str(other_group)} <= set(manageable(admin_client))


def test_group_tags_usable_on_items_by_members_only(
    client, another_client, admin_client, database, another_user_id, group_id, other_group
):
    """Members of a group can add its tags to items; non-members cannot introduce them,
    but may keep or remove one that is already on an item."""
    demo_tag = _create_tag(admin_client, "demo-team", scope="group", owner=group_id).json["data"][
        "immutable_id"
    ]
    other_tag = _create_tag(admin_client, "other-team", scope="group", owner=other_group).json[
        "data"
    ]["immutable_id"]

    # A sample both users can write; `user` is in the demo group only, `another_user`
    # in both groups.
    _make_shared_sample(client, database, "group-tag-item", another_user_id)

    def save(c, tag_ids):
        return c.post(
            "/save-item/",
            json={
                "item_id": "group-tag-item",
                "data": {"tags": [{"type": "tags", "immutable_id": t} for t in tag_ids]},
            },
        )

    # A member can add their group's tag.
    assert save(client, [demo_tag]).status_code == 200

    # A non-member cannot introduce the other group's tag...
    response = save(client, [demo_tag, other_tag])
    assert response.status_code == 403
    assert set(_item_tag_ids(client, "group-tag-item")) == {demo_tag}

    # ... but a member of that group can.
    assert save(another_client, [demo_tag, other_tag]).status_code == 200
    assert set(_item_tag_ids(client, "group-tag-item")) == {demo_tag, other_tag}

    # The non-member may keep the already-present tag, and may remove it.
    assert save(client, [demo_tag, other_tag]).status_code == 200
    assert save(client, [demo_tag]).status_code == 200
    assert set(_item_tag_ids(client, "group-tag-item")) == {demo_tag}

    # The same rule applies at item creation.
    def create(item_id, tag_id):
        return client.post(
            "/new-sample/",
            json={
                "type": "samples",
                "item_id": item_id,
                "tags": [{"type": "tags", "immutable_id": tag_id}],
            },
        )

    assert create("group-tag-create-ok", demo_tag).status_code == 201
    assert create("group-tag-create-bad", other_tag).status_code == 403


def test_item_tag_resolution_includes_owner_name(
    client, another_client, admin_client, database, another_user_id, group_id
):
    """Resolved item tags carry the `owner_name` of user and group tags (shown to any
    viewer of the item), which is not persisted on the item."""
    user_tag = _create_tag(client, "owned-by-user").json["data"]["immutable_id"]
    group_tag = _create_tag(admin_client, "owned-by-group", scope="group", owner=group_id).json[
        "data"
    ]["immutable_id"]
    global_tag = _create_tag(admin_client, "owned-by-nobody", scope="global").json["data"][
        "immutable_id"
    ]

    _make_shared_sample(client, database, "owner-name-item", another_user_id)
    response = client.post(
        "/save-item/",
        json={
            "item_id": "owner-name-item",
            "data": {
                "tags": [
                    {"type": "tags", "immutable_id": t, "owner_name": "stale"}
                    for t in (user_tag, group_tag, global_tag)
                ]
            },
        },
    )
    assert response.status_code == 200, response.json

    stored = database.items.find_one({"item_id": "owner-name-item"})
    assert all(set(t) == {"type", "immutable_id"} for t in stored["tags"])

    tags = {
        t["immutable_id"]: t
        for t in another_client.get("/get-item-data/owner-name-item").json["item_data"]["tags"]
    }
    assert tags[user_tag]["scope"] == "user"
    assert tags[user_tag]["owner_name"] == "Test User"
    assert tags[group_tag]["scope"] == "group"
    assert tags[group_tag]["owner_name"] == "Demo Group"
    assert "owner_name" not in tags[global_tag]


def test_deleting_group_deletes_its_tags(client, admin_client, database):
    """Deleting a group deletes its tags and drops their references from items."""
    temp_group_id = ObjectId()
    database.groups.insert_one(
        {"_id": temp_group_id, "display_name": "Temporary Group", "group_id": "temp-tags"}
    )

    group_tag = _create_tag(admin_client, "temp-team", scope="group", owner=temp_group_id).json[
        "data"
    ]["immutable_id"]
    global_tag = _create_tag(admin_client, "survivor", scope="global").json["data"]["immutable_id"]

    assert (
        client.post(
            "/new-sample/", json={"type": "samples", "item_id": "group-delete-item"}
        ).status_code
        == 201
    )
    # Tag the item directly (the admin is not a member of the group).
    database.items.update_one(
        {"item_id": "group-delete-item"},
        {
            "$set": {
                "tags": [
                    {"type": "tags", "immutable_id": ObjectId(group_tag)},
                    {"type": "tags", "immutable_id": ObjectId(global_tag)},
                ]
            }
        },
    )

    assert admin_client.delete(f"/groups/{temp_group_id}").status_code == 200

    assert database.tags.find_one({"_id": ObjectId(group_tag)}) is None
    assert database.tags.find_one({"_id": ObjectId(global_tag)}) is not None
    stored = database.items.find_one({"item_id": "group-delete-item"})
    assert stored["tags"] == [{"type": "tags", "immutable_id": ObjectId(global_tag)}]


# --- administrators manage every tag ---------------------------------------------


def test_admin_sudo_lists_all_tags(client, another_client, admin_client):
    """Administrators in super-user mode list every tag, including other users'
    user-defined tags (with their owner's name); nothing changes without sudo, for
    non-admins, or in the search used to add tags to items."""
    tag_id = _create_tag(client, "someone-elses").json["data"]["immutable_id"]

    def listed(c, **query):
        response = c.get("/tags", query_string=query)
        assert response.status_code == 200, response.json
        return {t["immutable_id"]: t for t in response.json["data"]}

    # Without sudo, an admin does not list another user's tag.
    assert tag_id not in listed(admin_client)

    # With sudo, they do, can manage it, and see whose it is.
    sudo_listing = listed(admin_client, sudo=1)
    assert sudo_listing[tag_id]["scope"] == "user"
    assert sudo_listing[tag_id]["owner_name"] == "Test User"
    assert sudo_listing[tag_id]["can_manage"] is True

    # `sudo` has no effect for non-admins.
    assert tag_id not in listed(another_client, sudo=1)

    # Super-user mode does not make the tag usable on items.
    search = admin_client.get(
        "/search-tags", query_string={"query": "someone-elses", "sudo": 1}
    ).json["data"]
    assert all(r["immutable_id"] != tag_id for r in search)


def test_admin_can_edit_and_delete_user_tags(client, admin_client, database):
    """Administrators can edit and delete other users' user-defined tags; deleting
    still pulls the references from items."""
    tag_id = _create_tag(client, "admin-managed").json["data"]["immutable_id"]

    assert (
        client.post(
            "/new-sample/", json={"type": "samples", "item_id": "admin-tag-del"}
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/save-item/",
            json={
                "item_id": "admin-tag-del",
                "data": {"tags": [{"type": "tags", "immutable_id": tag_id}]},
            },
        ).status_code
        == 200
    )

    response = admin_client.patch(f"/tags/{tag_id}", json={"data": {"description": "by admin"}})
    assert response.status_code == 200, response.json
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert stored["description"] == "by admin"
    # The tag still belongs to its owner.
    assert stored["scope"] == "user"

    assert admin_client.delete(f"/tags/{tag_id}").status_code == 200
    assert database.tags.find_one({"_id": ObjectId(tag_id)}) is None
    item = database.items.find_one({"item_id": "admin-tag-del"})
    assert [t for t in item.get("tags", []) if isinstance(t, dict)] == []


def _change_scope(c, tag_id, scope, owner=None, **extra):
    """Change a tag's scope through the tag edit endpoint (with optional extra edits)."""
    data = {"scope": scope, **extra}
    if owner is not None:
        data["owner"] = str(owner)
    return c.patch(f"/tags/{tag_id}", json={"data": data})


def test_admin_promotes_user_tag(
    client, another_client, admin_client, database, group_id, another_user_id
):
    """Administrators can move a user-defined tag to the global or a group scope; items
    keep the tag, which then follows the rules of its new scope."""
    tag_id = _create_tag(client, "promotable").json["data"]["immutable_id"]
    _make_shared_sample(client, database, "promoted-item", another_user_id)
    assert (
        client.post(
            "/save-item/",
            json={
                "item_id": "promoted-item",
                "data": {"tags": [{"type": "tags", "immutable_id": tag_id}]},
            },
        ).status_code
        == 200
    )

    # Only administrators can change a tag's scope, not even its owner.
    assert _change_scope(client, tag_id, "global").status_code == 403

    # user -> group
    response = _change_scope(admin_client, tag_id, "group", owner=group_id)
    assert response.status_code == 200, response.json
    admin_listing = {t["immutable_id"]: t for t in admin_client.get("/tags").json["data"]}
    assert admin_listing[tag_id]["scope"] == "group"
    assert admin_listing[tag_id]["owner"] == str(group_id)
    assert admin_listing[tag_id]["owner_name"] == "Demo Group"
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert stored["scope"] == "group"
    assert stored["owner"] == group_id

    # Another member of the group can now find and use it; the former owner (a plain
    # member) can no longer manage it.
    found = another_client.get("/search-tags", query_string={"query": "promotable"}).json["data"]
    assert tag_id in {r["immutable_id"] for r in found}
    listing = {t["immutable_id"]: t for t in client.get("/tags").json["data"]}
    assert listing[tag_id]["can_manage"] is False

    # group -> global
    response = _change_scope(admin_client, tag_id, "global")
    assert response.status_code == 200, response.json
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert stored["scope"] == "global"
    assert stored["owner"] is None

    # The item kept the tag, which now resolves as a global tag.
    tags = another_client.get("/get-item-data/promoted-item").json["item_data"]["tags"]
    assert [(t["immutable_id"], t["scope"]) for t in tags] == [(tag_id, "global")]


def test_change_tag_scope_validation(client, admin_client, group_id):
    """Invalid scope changes are rejected."""
    tag_id = _create_tag(client, "dup").json["data"]["immutable_id"]

    # Tags cannot be moved to the user scope, nor to an unknown scope.
    global_id = _create_tag(admin_client, "unmovable", scope="global").json["data"]["immutable_id"]
    assert _change_scope(admin_client, global_id, "user").status_code == 400
    assert _change_scope(admin_client, tag_id, "team").status_code == 400

    # A group scope needs an existing group.
    assert _change_scope(admin_client, tag_id, "group").status_code == 400
    assert _change_scope(admin_client, tag_id, "group", owner="nope").status_code == 400
    assert _change_scope(admin_client, tag_id, "group", owner=ObjectId()).status_code == 400

    # Unknown or invalid tag IDs.
    assert _change_scope(admin_client, str(ObjectId()), "global").status_code == 404
    assert _change_scope(admin_client, "nope", "global").status_code == 400

    # The name must not clash with another tag in the target scope.
    assert _create_tag(admin_client, "dup", scope="global").status_code == 201
    assert _change_scope(admin_client, tag_id, "global").status_code == 409
    assert _create_tag(admin_client, "dup", scope="group", owner=group_id).status_code == 201
    assert _change_scope(admin_client, tag_id, "group", owner=group_id).status_code == 409

    # Nothing changed.
    listing = {t["immutable_id"]: t for t in client.get("/tags").json["data"]}
    assert listing[tag_id]["scope"] == "user"


def test_change_scope_together_with_other_edits(client, admin_client, database, group_id):
    """A scope change can come with other edits in a single request; a rename is checked
    against the target scope, and a rejected request changes nothing. Re-sending the
    current scope (as the edit form does) is not a scope change."""
    tag_id = _create_tag(client, "combined").json["data"]["immutable_id"]

    # Re-sending the tag's current scope is allowed for its (non-admin) owner.
    response = client.patch(
        f"/tags/{tag_id}", json={"data": {"description": "same scope", "scope": "user"}}
    )
    assert response.status_code == 200, response.json

    # A rename that clashes in the target scope rejects the whole request.
    assert _create_tag(admin_client, "taken", scope="global").status_code == 201
    response = _change_scope(admin_client, tag_id, "global", name="taken", color="#000000")
    assert response.status_code == 409
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert (stored["name"], stored["scope"], stored.get("color")) == ("combined", "user", None)

    # Rename, recolor and move to a group in one go.
    response = _change_scope(
        admin_client, tag_id, "group", owner=group_id, name="renamed", color="#123456"
    )
    assert response.status_code == 200, response.json
    stored = database.tags.find_one({"_id": ObjectId(tag_id)})
    assert stored["name"] == "renamed"
    assert stored["color"] == "#123456"
    assert stored["scope"] == "group"
    assert stored["owner"] == group_id
