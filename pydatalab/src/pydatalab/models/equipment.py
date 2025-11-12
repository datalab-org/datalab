from typing import Any, ClassVar, Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits.ui_hints import HasUIHints, UIFieldConfig


class Equipment(Item, HasUIHints):
    """A model for representing an experimental sample."""

    type: Literal["equipment"] = "equipment"

    serial_numbers: str | None = Field(
        None,
        title="Serial no(s).",
        description="A string describing one or more serial numbers for the instrument.",
    )

    manufacturer: str | None = Field(
        None, description="The manufacturer of this piece of equipment"
    )

    location: str | None = Field(None, description="Place where the equipment is located")

    contact: str | None = Field(
        None,
        title="Contact Information",
        description="Contact information for equipment (e.g., email address or phone number).",
    )

    ui_layout: ClassVar[list[list[str]]] = [
        ["refcode", "item_id", "name", "date"],
        ["collections", "manufacturer", "location"],
        ["serial_numbers", "creators"],
        ["contact"],
        ["description"],
        ["table_of_contents"],
    ]

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {
        "refcode": UIFieldConfig(
            component="FormattedRefcode", width="col-md-2 col-sm-3", readonly=True
        ),
        "item_id": UIFieldConfig(component="input", width="col-md-2 col-sm-3", readonly=True),
        "name": UIFieldConfig(component="input", width="col-md-6 col-sm-6"),
        "date": UIFieldConfig(component="input", width="col-md-2 col-sm-3"),
        "collections": UIFieldConfig(
            component="CollectionList",
            width="col-md-2 col-sm-3",
        ),
        "manufacturer": UIFieldConfig(component="input", width="col-md-5 col-sm-5"),
        "location": UIFieldConfig(component="input", width="col-md-5 col-sm-5"),
        "serial_numbers": UIFieldConfig(component="input", width="col-md-8 col-sm-8"),
        "creators": UIFieldConfig(
            component="Creators",
            width="col-md-4 col-sm-4",
        ),
        "contact": UIFieldConfig(component="input", width="col-md-8 col-sm-8"),
        "description": UIFieldConfig(component="TinyMceInline", width="col-12"),
        "table_of_contents": UIFieldConfig(
            component="TableOfContents", width="col-12", hide_label=True
        ),
    }

    ui_virtual_fields: ClassVar[dict[str, dict[str, Any]]] = {
        "table_of_contents": {
            "title": "Table of Contents",
        },
    }

    ui_field_titles: ClassVar[dict[str, str]] = {
        "creators": "Maintainers",
    }
