"""Integration tests for custom item types registered via the server config.

Registers the in-repo example custom models (`pydatalab.models._example_custom`)
through `CONFIG.CUSTOM_ITEM_MODELS` / `load_custom_item_models` (the same path
used at server startup), then checks that they are advertised at `/info/types`
and can be created and read back through the generic item endpoints on the
standard test server.

The models are registered into the *global* item registries (and the `CONFIG`
singleton), so the fixture restores both afterwards to avoid leaking the custom
types into other test modules.
"""

import copy

import pytest

EXAMPLE_CUSTOM_MODELS = [
    "pydatalab.models._example_custom:MySample",
    "pydatalab.models._example_custom:MyItem",
]


@pytest.fixture(scope="module")
def custom_item_models():
    """Register the example custom item models with the running server, mirroring
    the `CONFIG.CUSTOM_ITEM_MODELS` startup path, and restore the registries and
    config afterwards.

    The item routes and `/info/types` read the registries live, so registering
    after the app has been created is sufficient and needs no second app.
    """
    import pydatalab.models as models
    from pydatalab.config import CONFIG

    models_snapshot = copy.copy(models.ITEM_MODELS)
    schemas_snapshot = copy.copy(models.ITEM_SCHEMAS)
    config_snapshot = list(CONFIG.CUSTOM_ITEM_MODELS)

    CONFIG.CUSTOM_ITEM_MODELS = list(EXAMPLE_CUSTOM_MODELS)
    models.load_custom_item_models(CONFIG.CUSTOM_ITEM_MODELS)

    try:
        yield
    finally:
        models.ITEM_MODELS.clear()
        models.ITEM_MODELS.update(models_snapshot)
        models.ITEM_SCHEMAS.clear()
        models.ITEM_SCHEMAS.update(schemas_snapshot)
        CONFIG.CUSTOM_ITEM_MODELS = config_snapshot


def test_custom_types_listed_in_info_types(client, custom_item_models):
    """The configured custom types and their extra fields appear at /info/types."""
    response = client.get("/info/types", follow_redirects=True)
    assert response.status_code == 200

    types = {entry["id"] for entry in response.json["data"]}
    assert "my_samples" in types
    assert "my_items" in types

    sample_schema = client.get("/info/types/my_samples", follow_redirects=True).json["data"][
        "attributes"
    ]["schema"]
    properties = sample_schema["properties"]
    # Extra top-level scalar, nested object, and inherited Sample fields are all present.
    assert "drying_time" in properties
    assert "custom_properties" in properties
    assert "chemform" in properties
    # The summary flag is carried through into the schema.
    assert properties["drying_time"].get("datalab_include_field_in_summary") is True

    item_schema = client.get("/info/types/my_items", follow_redirects=True).json["data"][
        "attributes"
    ]["schema"]
    assert "width" in item_schema["properties"]
    assert "height" in item_schema["properties"]


def test_create_and_read_custom_sample(client, custom_item_models):
    """A custom Sample subclass can be created and round-tripped, including a
    nested custom field, through the generic endpoints."""
    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "my_samples",
                "item_id": "custom-sample-1",
                "drying_time": 3.5,
                "custom_properties": {"batch": "B7", "purity": 0.95},
            }
        },
    )
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["sample_list_entry"]["type"] == "my_samples"

    response = client.get("/get-item-data/custom-sample-1")
    assert response.status_code == 200, response.json
    item_data = response.json["item_data"]
    assert item_data["type"] == "my_samples"
    assert item_data["drying_time"] == 3.5
    assert item_data["custom_properties"]["batch"] == "B7"
    assert item_data["custom_properties"]["purity"] == 0.95


def test_create_wholly_custom_item(client, custom_item_models):
    """An item type subclassing `Item` directly can be created and read back."""
    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "my_items",
                "item_id": "custom-item-1",
                "width": 12.0,
                "height": 4.0,
            }
        },
    )
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"

    response = client.get("/get-item-data/custom-item-1")
    assert response.status_code == 200, response.json
    item_data = response.json["item_data"]
    assert item_data["type"] == "my_items"
    assert item_data["width"] == 12.0
    assert item_data["height"] == 4.0


def test_unknown_custom_type_rejected(client, custom_item_models):
    """A type that was not registered is still rejected by the generic create
    endpoint."""
    response = client.post(
        "/new-sample/",
        json={"new_sample_data": {"type": "not_a_real_type", "item_id": "bad-1"}},
    )
    assert response.status_code == 400, response.json


def test_bad_custom_item_type_rejected():
    """A custom model is rejected at registration time if it reuses a reserved
    built-in `type`, or if it is not an `Item` subclass at all."""
    from typing import Literal

    from pydatalab.models import register_item_model
    from pydatalab.models.samples import Sample

    class ClashingSample(Sample):
        # Reuses the built-in "samples" type instead of declaring its own.
        type: Literal["samples"] = "samples"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="reserved built-in type"):
        register_item_model(ClashingSample)

    # Anything that is not an `Item` subclass is also rejected.
    with pytest.raises(TypeError):
        register_item_model(dict)


def test_info_types_base_type_for_custom_types(client, custom_item_models):
    """Custom types advertise their base_type; built-in types return base_type=None."""
    attrs = client.get("/info/types/my_samples", follow_redirects=True).json["data"]["attributes"]
    assert attrs["base_type"] == "samples"
    assert attrs["hidden_fields"] == []
    assert attrs["ui_color"] is None

    # MyItem inherits from Item directly — no built-in collection type in its MRO.
    attrs = client.get("/info/types/my_items", follow_redirects=True).json["data"]["attributes"]
    assert attrs["base_type"] is None

    # Built-in types themselves always return base_type=None.
    attrs = client.get("/info/types/samples", follow_redirects=True).json["data"]["attributes"]
    assert attrs["base_type"] is None


def test_save_item_null_field_is_cleared(client, custom_item_models):
    """Setting a custom field to null in a save call removes it from the DB.

    Without the $unset fix, model_dump(exclude_none=True) silently drops the
    null field from $set, leaving the old value in place in MongoDB.
    """
    client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "my_samples",
                "item_id": "unset-test-1",
                "drying_time": 5.0,
            }
        },
    )

    response = client.get("/get-item-data/unset-test-1")
    assert response.json["item_data"]["drying_time"] == 5.0

    # Now clear the field by saving with null.
    client.post(
        "/save-item/",
        json={
            "item_id": "unset-test-1",
            "data": {"type": "my_samples", "item_id": "unset-test-1", "drying_time": None},
        },
    )

    response = client.get("/get-item-data/unset-test-1")
    assert response.status_code == 200
    assert response.json["item_data"].get("drying_time") is None


def test_extra_fields_on_builtin_sample_are_ignored(client):
    """Stuffing custom-schema fields into a plain `samples` item does not persist
    them: the built-in `Sample` model ignores unknown fields (`extra="ignore"`),
    so custom data only "sticks" on a registered custom type."""
    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "samples",
                "item_id": "plain-sample-extra",
                "drying_time": 99.0,
                "custom_properties": {"batch": "X", "purity": 0.1},
            }
        },
    )
    assert response.status_code == 201, response.json

    response = client.get("/get-item-data/plain-sample-extra")
    assert response.status_code == 200, response.json
    item_data = response.json["item_data"]
    assert item_data["type"] == "samples"
    assert "drying_time" not in item_data
    assert "custom_properties" not in item_data
