# This file was edited with the assistance of an AI model and requires human review from the contributor.
"""Example custom item models, used to demonstrate and test the registration of
deployment-specific item types via ``CONFIG.CUSTOM_ITEM_MODELS``.

These are intentionally *not* registered by default; a deployment (or the test
suite) opts in by listing their dotted paths in ``CUSTOM_ITEM_MODELS``::

    CUSTOM_ITEM_MODELS = [
        "pydatalab.models._example_custom:MySample",
        "pydatalab.models._example_custom:MyItem",
    ]

Once registered they are served through the generic item endpoints
(``/new-sample/``, ``/items/<refcode>``, ``/save-item/``) and advertised at
``/info/types`` with no further code.

Note that the types declared below are deliberately *not* namespaced: they are
rewritten at registration time, so they are served as ``_my_samples`` and
``_my_items``.
"""

from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.samples import Sample
from pydatalab.models.utils import BaseModel

# A quantity shared by several fields: stored in mm, displayable in cm or m.
_LENGTH_QUANTITY = {
    "canonical_unit": "mm",
    "display_units": {
        "mm": {"scale": 1.0},
        "cm": {"scale": 10.0},
        "m": {"scale": 1000.0},
    },
}


class CustomProperties(BaseModel):
    """A nested object demonstrating that custom item fields may themselves be
    structured models, not just scalars."""

    batch: str | None = None
    """An arbitrary batch identifier."""

    purity: float | None = None
    """A fractional purity between 0 and 1."""


class MySample(Sample):
    """An example custom sample type with a couple of extra fields, including a
    nested object, demonstrating top-level schema extension of a built-in."""

    type: Literal["my_samples"] = "my_samples"  # type: ignore[assignment]

    drying_time: float | None = Field(
        None,
        json_schema_extra={
            "datalab_include_field_in_summary": True,
            "datalab_quantity": {
                "canonical_unit": "h",
                "display_units": {
                    "h": {"scale": 1.0},
                    "min": {"scale": 1 / 60},
                    "days": {"scale": 24.0},
                },
            },
        },
    )
    """An example extra top-level scalar field, surfaced in list views. It is always
    stored in hours; as no `display_unit_field` is declared, the unit it is displayed
    in is not stored with the item."""

    custom_properties: CustomProperties | None = None
    """An example extra nested field."""


class MyItem(Item):
    """An example wholly custom item type (not sample-derived) with custom
    'dimension' fields."""

    type: Literal["my_items"] = "my_items"  # type: ignore[assignment]

    width: float | None = Field(
        None,
        json_schema_extra={
            "datalab_include_field_in_summary": True,
            "datalab_quantity": _LENGTH_QUANTITY,
        },
    )
    """An example custom dimension (stored in mm), surfaced in list views."""

    height: float | None = Field(None, json_schema_extra={"datalab_quantity": _LENGTH_QUANTITY})
    """An example custom dimension (stored in mm)."""
