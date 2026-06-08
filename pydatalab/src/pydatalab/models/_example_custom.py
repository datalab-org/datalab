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
"""

from typing import Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.samples import Sample
from pydatalab.models.utils import BaseModel


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
        None, json_schema_extra={"datalab_include_field_in_summary": True}
    )
    """An example extra top-level scalar field (hours), surfaced in list views."""

    custom_properties: CustomProperties | None = None
    """An example extra nested field."""


class MyItem(Item):
    """An example wholly custom item type (not sample-derived) with custom
    'dimension' fields."""

    type: Literal["my_items"] = "my_items"  # type: ignore[assignment]

    width: float | None = Field(None, json_schema_extra={"datalab_include_field_in_summary": True})
    """An example custom dimension (mm), surfaced in list views."""

    height: float | None = None
    """An example custom dimension (mm)."""
