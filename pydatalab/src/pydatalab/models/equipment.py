from typing import Any, ClassVar, Literal

from pydatalab.models.items import Item
from pydatalab.models.traits.ui_hints import HasUIHints, UIFieldConfig


class Equipment(Item, HasUIHints):
    """A model for representing laboratory equipment."""

    type: Literal["equipment"] = "equipment"

    ui_layout: ClassVar[list[list[str]]] = [
        ["name", "date"],
        ["refcode", "creators", "collections"],
        ["description"],
        ["table_of_contents"],
    ]

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {
        "name": UIFieldConfig(component="input", width="col-sm-8 pr-2 col-6"),
        "date": UIFieldConfig(component="input", width="col-sm-4 col-6"),
        "refcode": UIFieldConfig(
            component="FormattedRefcode", width="col-md-3 col-sm-4 col-6", readonly=True
        ),
        "creators": UIFieldConfig(
            component="ToggleableCreatorsFormGroup",
            width="col-md-3 col-sm-3 col-6 pb-3",
            has_builtin_label=True,
        ),
        "collections": UIFieldConfig(
            component="ToggleableCollectionFormGroup",
            width="col-md-6 col-sm-7 pr-2",
            has_builtin_label=True,
        ),
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

    ui_table_of_contents: ClassVar[list[dict[str, str]]] = [
        {"title": "Equipment Information", "targetID": "equipment-information"},
        {"title": "Table of Contents", "targetID": "table-of-contents"},
    ]
