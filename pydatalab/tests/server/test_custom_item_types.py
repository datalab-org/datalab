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
