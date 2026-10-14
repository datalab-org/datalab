from datetime import datetime, timezone

import pytest

from pydatalab.models import Sample
from pydatalab.routes.v0_1.query_filter import InvalidFilter, compile_filter
from pydatalab.routes.v0_1.query_schema import QUERY_VIEWS, _build_field_registry_for_view


@pytest.fixture(scope="module")
def sample_registry():
    return _build_field_registry_for_view("samples", QUERY_VIEWS["samples"], ["samples"])


@pytest.fixture
def optimade_samples(database, user_id, admin_user_id):
    samples = [
        Sample(
            item_id="opt_lfp_1",
            refcode="test:OPT1",
            name="Alpha LFP",
            chemform="LiFePO4",
            description="cathode",
            date="2026-01-10T00:00:00",
            creator_ids=[user_id],
        ),
        Sample(
            item_id="opt_nmc",
            refcode="test:OPT2",
            name="Beta NMC",
            chemform="LiNiO2",
            date="2026-03-10T00:00:00",
            creator_ids=[user_id],
            synthesis_constituents=[
                {
                    "item": {"type": "samples", "item_id": "opt_lfp_1", "name": "Alpha LFP"},
                    "quantity": 1.0,
                }
            ],
        ),
        Sample(
            item_id="opt_lfp_2",
            refcode="test:OPT3",
            name="Gamma lfp (old)",
            chemform="LiFePO4",
            date="2025-06-01T00:00:00",
            # Shared with the admin, so it is the only sample that is not "mine" for them.
            creator_ids=[user_id, admin_user_id],
        ),
    ]
    item_ids = [s.item_id for s in samples]
    database.items.delete_many({"item_id": {"$in": item_ids}})
    database.items.insert_many([s.model_dump(exclude_unset=False) for s in samples])
    yield samples
    database.items.delete_many({"item_id": {"$in": item_ids}})


def _search(client, type_id="samples", **params):
    return client.get(f"/query/{type_id}", query_string=params)


def _ids(response):
    assert response.status_code == 200, response.json
    return {item.get("item_id") or item.get("collection_id") for item in response.json["items"]}


def test_searchable_types_per_table(client):
    response = client.get("/query/types?data_type=samples")
    assert response.status_code == 200
    assert response.json["types"] == [
        {"id": "samples", "label": "Sample"},
        {"id": "cells", "label": "Cell"},
    ]
    assert client.get("/query/types?data_type=not_a_table").json["types"] == []


def test_schema_lists_properties(client):
    cases = {
        "samples": "chemform",
        "equipment": "manufacturer",
        # OPTIMADE property names are lowercase, so `CAS` is exposed as `cas`
        "starting_materials": "cas",
        "collections": "title",
    }
    for type_id, expected in cases.items():
        response = client.get(f"/query/{type_id}/schema")
        assert response.status_code == 200
        assert expected in {field["id"] for field in response.json["fields"]}


def test_schema_reports_optimade_operators(client):
    response = client.get("/query/samples/schema")
    assert response.json["max_depth"] == 5
    fields = {field["id"]: field for field in response.json["fields"]}

    def operator_ids(field_id):
        return [op["id"] for op in fields[field_id]["operators"]]

    assert operator_ids("name") == [
        "=",
        "!=",
        "CONTAINS",
        "STARTS WITH",
        "ENDS WITH",
        "IS KNOWN",
        "IS UNKNOWN",
    ]
    assert fields["date"]["value_type"] == "timestamp"
    assert fields["molar_mass"]["value_type"] == "number"
    assert "<=" in operator_ids("molar_mass")
    assert fields["synthesis_constituents.item.name"]["is_list"]
    assert "HAS ANY" in operator_ids("synthesis_constituents.item.name")
    # Only what is stored can be searched: tags are stored as bare references, and
    # immutable IDs as ObjectIds.
    assert not [f for f in fields if f.startswith("tags") or f.endswith("immutable_id")]
    constituent_has = next(
        op for op in fields["synthesis_constituents.item.item_id"]["operators"] if op["id"] == "HAS"
    )
    assert constituent_has["editor"] == "constituent-selector"


def test_search_across_types(
    client,
    insert_default_sample,
    insert_default_equipment,
    insert_default_starting_material,
):
    cases = [
        ("samples", 'name = "other_sample"', insert_default_sample.item_id),
        ("equipment", 'manufacturer = "science inc."', insert_default_equipment.item_id),
        ("starting_materials", 'chemform = "Na2CO3"', insert_default_starting_material.item_id),
    ]
    for type_id, filter_, item_id in cases:
        response = _search(client, type_id, filter=filter_)
        assert item_id in _ids(response)
        assert {item["type"] for item in response.json["items"]} == {type_id}


def test_search_collections(client, database, default_collection):
    database.collections.insert_one(default_collection.model_dump(exclude_unset=False))
    try:
        response = _search(client, "collections", filter='title CONTAINS "My"')
        assert default_collection.collection_id in _ids(response)
    finally:
        database.collections.delete_one({"collection_id": default_collection.collection_id})


def test_search_response(client, optimade_samples):
    response = _search(client, filter='name CONTAINS "LFP"')
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["total"] == 1
    assert response.json["next_offset"] is None
    # Only what identifies each match is returned.
    assert response.json["items"] == [{"item_id": "opt_lfp_1", "type": "samples"}]


def test_search_pagination_and_sort(client, optimade_samples):
    filter_ = 'item_id STARTS WITH "opt_"'
    first = _search(client, filter=filter_, sort="date", limit=2)
    assert [i["item_id"] for i in first.json["items"]] == ["opt_lfp_2", "opt_lfp_1"]
    assert first.json["total"] == 3
    assert first.json["next_offset"] == 2

    second = _search(client, filter=filter_, sort="date", limit=2, offset=2)
    assert [i["item_id"] for i in second.json["items"]] == ["opt_nmc"]
    assert second.json["next_offset"] is None

    descending = _search(client, filter=filter_, sort="-date")
    assert [i["item_id"] for i in descending.json["items"]] == ["opt_nmc", "opt_lfp_1", "opt_lfp_2"]

    count_only = _search(client, filter=filter_, limit=0)
    assert count_only.json["items"] == []
    assert count_only.json["total"] == 3


@pytest.mark.parametrize(
    "params",
    [
        {"sort": "description"},
        {"sort": "-not_a_field"},
        {"limit": "1001"},
        {"offset": str(2**64)},
        {"limit": "-1"},
        {"offset": "x"},
    ],
)
def test_invalid_parameters(client, params):
    response = _search(client, **params)
    assert response.status_code == 400
    assert response.json["status"] == "error"
    assert response.json["message"]


@pytest.mark.parametrize(
    "filter_",
    [
        "1 = 1",
        'name = "x" AND 2 > 1',
        # Too large for the database's 64-bit integers
        "molar_mass > 99999999999999999999999",
    ],
)
def test_filters_the_database_cannot_run_return_400(client, filter_):
    response = _search(client, filter=filter_)
    assert response.status_code == 400, response.json
    assert response.json["status"] == "error"


def test_users_and_groups_are_admin_only(client, admin_client):
    for type_id in ("users", "groups"):
        assert _search(client, type_id).status_code == 404
        assert client.get(f"/query/{type_id}/schema").status_code == 404
        assert _search(admin_client, type_id).status_code == 200
        assert admin_client.get(f"/query/{type_id}/schema").status_code == 200
    assert client.get("/query/types?data_type=users").json["types"] == []
    assert [t["id"] for t in admin_client.get("/query/types?data_type=users").json["types"]] == [
        "users"
    ]


def test_user_search_returns_only_ids(admin_client):
    response = _search(admin_client, "users")
    assert response.status_code == 200
    assert response.json["items"]
    for item in response.json["items"]:
        assert set(item) == {"_id"}


def test_mine_keeps_only_own_entries(client, admin_client, optimade_samples):
    filter_ = 'item_id STARTS WITH "opt_"'
    assert _ids(_search(client, filter=filter_, mine="true")) == {
        "opt_lfp_1",
        "opt_nmc",
        "opt_lfp_2",
    }
    # ?sudo=1 lets the admin see every sample, but only one of them is theirs.
    assert _ids(_search(admin_client, filter=filter_, sudo="1")) == {
        "opt_lfp_1",
        "opt_nmc",
        "opt_lfp_2",
    }
    assert _ids(_search(admin_client, filter=filter_, sudo="1", mine="1")) == {"opt_lfp_2"}


def test_unknown_type(client):
    assert _search(client, "not_a_type").status_code == 404
    assert client.get("/query/not_a_type/schema").status_code == 404


@pytest.mark.parametrize(
    "filter_,expected",
    [
        ("", {"opt_lfp_1", "opt_nmc", "opt_lfp_2"}),
        ('chemform = "LiFePO4"', {"opt_lfp_1", "opt_lfp_2"}),
        ('chemform != "LiFePO4"', {"opt_nmc"}),
        # CONTAINS is case-sensitive
        ('name CONTAINS "LFP"', {"opt_lfp_1"}),
        ('name STARTS WITH "Beta"', {"opt_nmc"}),
        ('name STARTS "Beta"', {"opt_nmc"}),
        ('name ENDS WITH "(old)"', {"opt_lfp_2"}),
        ('date >= "2026-01-01T00:00:00Z"', {"opt_lfp_1", "opt_nmc"}),
        ('date < "2026-01-01T00:00:00Z" OR name = "Beta NMC"', {"opt_lfp_2", "opt_nmc"}),
        # AND binds tighter than OR
        (
            'name = "Beta NMC" OR chemform = "LiFePO4" AND date > "2026-01-01T00:00:00Z"',
            {"opt_nmc", "opt_lfp_1"},
        ),
        (
            '(name = "Beta NMC" OR chemform = "LiFePO4") AND date > "2026-01-01T00:00:00Z"',
            {"opt_nmc", "opt_lfp_1"},
        ),
        ('NOT chemform = "LiFePO4"', {"opt_nmc"}),
        ('NOT (chemform = "LiFePO4" OR name = "Beta NMC")', set()),
        ("description IS KNOWN", {"opt_lfp_1"}),
        ('description IS UNKNOWN AND name CONTAINS "a"', {"opt_nmc", "opt_lfp_2"}),
        # Properties with an unserved provider prefix are treated as unknown, not as errors
        ("_other_provider_field IS UNKNOWN", {"opt_lfp_1", "opt_nmc", "opt_lfp_2"}),
        ('_other_provider_field = "x"', set()),
        # Searches on stored constituent references find the samples made from an item.
        ('synthesis_constituents.item.item_id HAS "opt_lfp_1"', {"opt_nmc"}),
        ('synthesis_constituents.item.name HAS ANY "Alpha LFP", "x"', {"opt_nmc"}),
        ("synthesis_constituents.quantity HAS 1.0", {"opt_nmc"}),
    ],
)
def test_optimade_filter_execution(client, optimade_samples, filter_, expected):
    found = _ids(_search(client, filter=filter_)) & {s.item_id for s in optimade_samples}
    assert found == expected


@pytest.mark.parametrize(
    "filter_",
    [
        "name = ",
        'name == "x"',
        'not_a_field = "x"',
        # Property names must be lowercase identifiers
        'Name = "x"',
        'date > "last week"',
        "name = chemform",
    ],
)
def test_invalid_filters_return_400(client, filter_):
    response = _search(client, filter=filter_)
    assert response.status_code == 400
    assert response.json["status"] == "error"


def test_compile_filter_escapes_regex_and_strings(sample_registry):
    assert compile_filter(r'name CONTAINS "a.b(\"c\\"', sample_registry) == {
        "name": {"$regex": r'a\.b\("c\\'}
    }


def test_compile_filter_converts_timestamps(sample_registry):
    assert compile_filter('date >= "2026-01-31T12:00:00+02:00"', sample_registry) == {
        "date": {"$gte": datetime(2026, 1, 31, 10, tzinfo=timezone.utc)}
    }


def test_compile_filter_maps_property_names(sample_registry):
    assert compile_filter('ghs_codes CONTAINS "H3"', sample_registry) == {
        "GHS_codes": {"$regex": "H3"}
    }


def test_compile_filter_list_operators(sample_registry):
    assert compile_filter('synthesis_constituents.item.name HAS ALL "a", "b"', sample_registry) == {
        "synthesis_constituents.item.name": {"$all": ["a", "b"]}
    }
    assert compile_filter('synthesis_constituents.item.name HAS ANY "a", "b"', sample_registry) == {
        "synthesis_constituents.item.name": {"$in": ["a", "b"]}
    }


def test_compile_filter_empty(sample_registry):
    assert compile_filter("", sample_registry) == {}
    assert compile_filter(None, sample_registry) == {}
    with pytest.raises(InvalidFilter):
        compile_filter("x" * 10_001, sample_registry)
