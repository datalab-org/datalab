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
    assert "example:samples" in types
    assert "example:items" in types

    sample_schema = client.get("/info/types/example:samples", follow_redirects=True).json["data"][
        "attributes"
    ]["schema"]
    properties = sample_schema["properties"]
    # Extra top-level scalar, nested object, and inherited Sample fields are all present.
    assert "drying_time" in properties
    assert "custom_properties" in properties
    assert "chemform" in properties
    # The summary flag is carried through into the schema.
    assert properties["drying_time"].get("datalab_include_field_in_summary") is True

    item_schema = client.get("/info/types/example:items", follow_redirects=True).json["data"][
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
                "type": "example:samples",
                "item_id": "custom-sample-1",
                "drying_time": 3.5,
                "custom_properties": {"batch": "B7", "purity": 0.95},
            }
        },
    )
    assert response.status_code == 201, response.json
    assert response.json["status"] == "success"
    assert response.json["sample_list_entry"]["type"] == "example:samples"
    assert response.json["sample_list_entry"]["drying_time"] == 3.5

    response = client.get("/get-item-data/custom-sample-1")
    assert response.status_code == 200, response.json
    item_data = response.json["item_data"]
    assert item_data["type"] == "example:samples"
    assert item_data["drying_time"] == 3.5
    assert item_data["custom_properties"]["batch"] == "B7"
    assert item_data["custom_properties"]["purity"] == 0.95

    response = client.get("/samples/")
    assert response.status_code == 200, response.json
    summaries = {item["item_id"]: item for item in response.json["samples"]}
    assert summaries["custom-sample-1"]["type"] == "example:samples"
    assert summaries["custom-sample-1"]["drying_time"] == 3.5


def test_create_wholly_custom_item(client, custom_item_models):
    """An item type subclassing `Item` directly can be created and read back."""
    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "example:items",
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
    assert item_data["type"] == "example:items"
    assert item_data["width"] == 12.0
    assert item_data["height"] == 4.0

    # All custom item types are surfaced through the Samples page for now,
    # including types that inherit directly from Item.
    response = client.get("/samples/")
    assert response.status_code == 200, response.json
    listed_items = {item["item_id"]: item for item in response.json["samples"]}
    assert listed_items["custom-item-1"]["type"] == "example:items"


def test_custom_type_as_synthesis_constituent(client, custom_item_models):
    """A custom sample-derived type can be used as a synthesis constituent of
    another item, since the allowed constituent types are resolved from the live
    item registry rather than a fixed enum."""
    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "example:samples",
                "item_id": "custom-constituent-1",
                "name": "A custom precursor",
            }
        },
    )
    assert response.status_code == 201, response.json

    response = client.post(
        "/new-sample/",
        json={
            "new_sample_data": {
                "type": "samples",
                "item_id": "sample-with-custom-constituent",
                "synthesis_constituents": [
                    {
                        "item": {"item_id": "custom-constituent-1", "type": "example:samples"},
                        "quantity": 1.0,
                        "unit": "g",
                    }
                ],
            }
        },
    )
    assert response.status_code == 201, response.json

    response = client.get("/get-item-data/sample-with-custom-constituent")
    assert response.status_code == 200, response.json
    item_data = response.json["item_data"]
    assert item_data["synthesis_constituents"][0]["item"]["item_id"] == "custom-constituent-1"

    # The constituent should also have been turned into a parent relationship
    parents = [
        relationship
        for relationship in item_data["relationships"]
        if relationship["relation"] == "parent"
    ]
    assert len(parents) == 1
    assert parents[0]["item_id"] == "custom-constituent-1"
    assert parents[0]["type"] == "example:samples"


def test_equipment_rejected_as_synthesis_constituent(client):
    """Types without substance information (e.g. `equipment`) remain invalid as
    synthesis constituents."""
    from pydantic import ValidationError

    from pydatalab.models.utils import Constituent

    with pytest.raises(ValidationError, match="`type` must be one of"):
        Constituent(
            item={"item_id": "some-equipment", "type": "equipment"},
            quantity=1.0,
            unit="g",
        )


def test_unknown_custom_type_rejected(client, custom_item_models):
    """A type that was not registered is still rejected by the generic create
    endpoint."""
    response = client.post(
        "/new-sample/",
        json={"new_sample_data": {"type": "missing:type", "item_id": "bad-1"}},
    )
    assert response.status_code == 400, response.json


def test_bad_custom_item_type_rejected():
    """A custom model is rejected at registration time if it reuses a reserved
    built-in `type`, or is not an `Item` subclass at all."""
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


def test_builtin_item_type_identifiers_are_bare():
    """Built-in identifiers do not use the custom namespace separator."""
    from pydatalab.models import BUILTIN_ITEM_TYPES

    assert all(":" not in item_type for item_type in BUILTIN_ITEM_TYPES)


@pytest.mark.parametrize(
    "item_type",
    [
        "electrode",
        "battery_electrode",
        "_battery:electrode",
        "battery_:electrode",
        "battery:-electrode",
        "battery:electrode_",
        "Battery:electrode",
        "battery:Electrode",
        "battery::electrode",
        "battery:electrode:variant",
        ":electrode",
        "battery:",
        "acme--battery:electrode",
        "acme__battery:electrode",
        "battery:coin--cell",
        "battery:coin__cell",
        "battery.electrode",
        "battery:electrode.variant",
    ],
)
def test_invalid_custom_item_type_identifier_rejected(item_type):
    """Custom identifiers contain one colon between lowercase name components."""
    from typing import Literal

    from pydantic import create_model

    from pydatalab.models import register_item_model
    from pydatalab.models.samples import Sample

    InvalidSample = create_model(
        "InvalidSample",
        __base__=Sample,
        type=(Literal[item_type], item_type),  # type: ignore[valid-type]
    )

    with pytest.raises(ValueError, match="invalid type"):
        register_item_model(InvalidSample)


def test_info_types_base_type_for_custom_types(client, custom_item_models):
    """Custom types advertise their UI base and inherited fields."""
    attrs = client.get("/info/types/example:samples", follow_redirects=True).json["data"][
        "attributes"
    ]
    assert attrs["base_type"] == "samples"
    assert "chemform" in attrs["base_fields"]
    assert "drying_time" not in attrs["base_fields"]
    assert attrs["hidden_fields"] == []
    assert attrs["ui_color"] is None

    # Direct Item subclasses use the virtual `items` UI base. It is metadata for
    # selecting the generic component, not a concrete type exposed in ITEM_MODELS.
    attrs = client.get("/info/types/example:items", follow_redirects=True).json["data"][
        "attributes"
    ]
    assert attrs["base_type"] == "items"
    assert "name" in attrs["base_fields"]
    assert "location" in attrs["base_fields"]
    assert "width" not in attrs["base_fields"]

    # Built-in types themselves always return base_type=None.
    attrs = client.get("/info/types/samples", follow_redirects=True).json["data"]["attributes"]
    assert attrs["base_type"] is None
    assert attrs["base_fields"] == []


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


def test_namespaced_identifier_is_canonical():
    """The model, registry and schema use the same canonical identifier."""
    from typing import Literal

    from pydatalab.models import ITEM_MODELS, ITEM_SCHEMAS, register_item_model
    from pydatalab.models.samples import Sample

    class BatteryElectrode(Sample):
        type: Literal["battery:electrode"] = "battery:electrode"  # type: ignore[assignment]

    class ConflictingBatteryElectrode(Sample):
        type: Literal["battery:electrode"] = "battery:electrode"  # type: ignore[assignment]

    try:
        register_item_model(BatteryElectrode)

        assert ITEM_MODELS["battery:electrode"] is BatteryElectrode
        assert (
            ITEM_SCHEMAS["battery:electrode"]["properties"]["type"]["default"]
            == "battery:electrode"
        )

        item = BatteryElectrode(item_id="canonical-identifier")
        assert item.type == "battery:electrode"
        assert item.model_dump()["type"] == "battery:electrode"
        assert isinstance(item, Sample)

        # Registering a custom subclass must not disturb its built-in base.
        assert Sample.model_fields["type"].default == "samples"
        assert Sample(item_id="still-a-sample").type == "samples"

        register_item_model(BatteryElectrode)
        assert ITEM_MODELS["battery:electrode"] is BatteryElectrode

        with pytest.raises(ValueError, match="already registered"):
            register_item_model(ConflictingBatteryElectrode)
    finally:
        ITEM_MODELS.pop("battery:electrode", None)
        ITEM_SCHEMAS.pop("battery:electrode", None)


@pytest.mark.parametrize(
    "item_type",
    ["acme-battery:coin-cell", "acme_battery:coin_cell", "acme-lab_1:coin_cell-v2"],
)
def test_namespace_and_type_name_separators_are_registered(item_type):
    """Either side of the colon may contain internal dashes or underscores."""
    from typing import Literal

    from pydantic import create_model

    from pydatalab.models import ITEM_MODELS, ITEM_SCHEMAS, register_item_model
    from pydatalab.models.samples import Sample

    BatteryCoinCell = create_model(
        "BatteryCoinCell",
        __base__=Sample,
        type=(Literal[item_type], item_type),  # type: ignore[valid-type]
    )

    try:
        register_item_model(BatteryCoinCell)
        assert ITEM_MODELS[item_type] is BatteryCoinCell
        assert ITEM_SCHEMAS[item_type]["properties"]["type"]["default"] == item_type
    finally:
        ITEM_MODELS.pop(item_type, None)
        ITEM_SCHEMAS.pop(item_type, None)


def test_refresh_item_models_ignores_custom_types(custom_item_models):
    """`refresh_item_models` rebuilds only the built-in entries: it must neither
    drop registered custom types nor rediscover merely imported custom models
    through the `Item` subclass walk."""
    from typing import Literal

    from pydatalab.models import ITEM_MODELS, ITEM_SCHEMAS, refresh_item_models
    from pydatalab.models.samples import Sample

    class NeverRegisteredSample(Sample):
        """A valid custom model that has been imported but not registered."""

        type: Literal["unregistered:sample"] = "unregistered:sample"  # type: ignore[assignment]

    refresh_item_models()

    assert "unregistered:sample" not in ITEM_MODELS
    assert "unregistered:sample" not in ITEM_SCHEMAS

    assert "samples" in ITEM_MODELS
    assert "example:samples" in ITEM_MODELS
    assert "example:samples" in ITEM_SCHEMAS
    assert "example:items" in ITEM_MODELS
    assert "example:items" in ITEM_SCHEMAS
