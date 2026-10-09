"""Tests for the `datalab_behave_as` model hint, which lets a custom item type follow the
listing and permission behaviour of the built-in type it inherits from."""

import copy
from typing import Literal

import pytest
from pydantic import ConfigDict

from pydatalab.models.equipment import Equipment
from pydatalab.models.starting_materials import StartingMaterial


class HintedStartingMaterial(StartingMaterial):
    model_config = ConfigDict(json_schema_extra={"datalab_behave_as": "starting_materials"})
    type: Literal["hinted_starting_materials"] = "hinted_starting_materials"  # type: ignore[assignment]


class HintedEquipment(Equipment):
    model_config = ConfigDict(json_schema_extra={"datalab_behave_as": "equipment"})
    type: Literal["hinted_equipment"] = "hinted_equipment"  # type: ignore[assignment]


class PlainStartingMaterial(StartingMaterial):
    """Without the hint: keeps today's sample-like behaviour."""

    type: Literal["plain_starting_materials"] = "plain_starting_materials"  # type: ignore[assignment]


@pytest.fixture(scope="module")
def behave_as_models():
    """Register the models, restoring the global registries afterwards."""
    import pydatalab.models as models
    from pydatalab.permissions import INVENTORY_TYPES

    snapshots = [
        (r, copy.copy(r)) for r in (models.ITEM_MODELS, models.ITEM_SCHEMAS, INVENTORY_TYPES)
    ]
    for model in (HintedStartingMaterial, HintedEquipment, PlainStartingMaterial):
        models.register_item_model(model)
    yield
    for registry, snapshot in snapshots:
        registry.clear()
        registry.update(snapshot)


def _create(client, item_type, item_id):
    response = client.post("/new-sample/", json={"type": item_type, "item_id": item_id})
    assert response.status_code == 201, response.json
    return response.json["sample_list_entry"]


def _listed(client, endpoint, key="items"):
    return {item["item_id"] for item in client.get(endpoint).json[key]}


def test_hinted_types_are_listed_with_their_builtin_type(client, behave_as_models):
    _create(client, "_hinted_starting_materials", "hinted-sm")
    _create(client, "_hinted_equipment", "hinted-eq")
    _create(client, "_plain_starting_materials", "plain-sm")

    samples = _listed(client, "/samples/", key="samples")
    assert "hinted-sm" in _listed(client, "/starting-materials/")
    assert "hinted-eq" in _listed(client, "/equipment/")
    assert "plain-sm" in samples
    assert not {"hinted-sm", "hinted-eq"} & samples

    info = client.get("/info/types/_hinted_starting_materials", follow_redirects=True).json
    assert info["data"]["attributes"]["behave_as"] == "starting_materials"


def test_hinted_types_have_inventory_permissions(
    client, another_client, unverified_client, group_id, behave_as_models
):
    entry = _create(client, "_hinted_starting_materials", "perm-hinted-sm")
    assert entry["creator_ids"] == []
    refcode = entry["refcode"]

    # Readable and editable by other users...
    assert another_client.get(f"/items/{refcode}").status_code == 200
    response = another_client.post(
        "/save-item/", json={"item_id": "perm-hinted-sm", "data": {"name": "edited"}}
    )
    assert response.status_code == 200, response.json

    # ...unless restricted to a group they are not in
    response = client.patch(
        f"/items/{refcode}/permissions", json={"groups": [{"immutable_id": str(group_id)}]}
    )
    assert response.status_code == 200, response.json
    assert unverified_client.get(f"/items/{refcode}").status_code == 404

    # Without the hint, the item stays private to its creator
    plain = _create(client, "_plain_starting_materials", "perm-plain-sm")
    assert another_client.get(f"/items/{plain['refcode']}").status_code == 404


def test_behave_as_requires_inheritance():
    from pydatalab.models import register_item_model

    class NotEquipment(StartingMaterial):
        model_config = ConfigDict(json_schema_extra={"datalab_behave_as": "equipment"})
        type: Literal["_not_equipment"] = "_not_equipment"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="does not inherit from"):
        register_item_model(NotEquipment)
