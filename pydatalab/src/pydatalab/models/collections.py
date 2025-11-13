from typing import Any, ClassVar, Literal

from pydantic import (
    Field,
    model_validator,
)

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasBlocks, HasOwner
from pydatalab.models.traits.ui_hints import HasUIHints, UIFieldConfig
from pydatalab.models.utils import HumanReadableIdentifier


class Collection(Entry, HasOwner, HasBlocks, HasUIHints):
    type: Literal["collections"] = "collections"

    collection_id: HumanReadableIdentifier = Field(
        None, description="A short human-readable/usable name for the collection."
    )

    title: str | None = Field(None, description="A descriptive title for the collection.")

    description: str | None = Field(
        None,
        description="A description of the collection, either in plain-text or a markup language.",
    )

    num_items: int | None = Field(
        None, description="Inlined number of items associated with this collection."
    )

    ui_layout: ClassVar[list[list[str]]] = [
        ["title"],
        ["creators"],
        ["description"],
        ["items_table"],
    ]

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {
        "title": UIFieldConfig(component="input", width="col"),
        "creators": UIFieldConfig(component="Creators", width="col", has_builtin_label=True),
        "description": UIFieldConfig(component="TinyMceInline", width="col-12"),
        "items_table": UIFieldConfig(
            component="DynamicDataTable",
            width="col-12",
            hide_label=True,
            component_props={
                "columns": [
                    {
                        "field": "item_id",
                        "header": "ID",
                        "body": "FormattedItemName",
                        "filter": True,
                    },
                    {"field": "type", "header": "Type", "filter": True},
                    {"field": "name", "header": "Sample name"},
                    {"field": "chemform", "header": "Formula", "body": "ChemicalFormula"},
                    {"field": "date", "header": "Date"},
                    {"field": "creators", "header": "Creators", "body": "Creators"},
                    {"field": "nblocks", "header": "# of blocks"},
                ],
                "global_filter_fields": [
                    "item_id",
                    "name",
                    "refcode",
                    "blocks",
                    "chemform",
                    "characteristic_chemical_formula",
                ],
                "show_buttons": True,
            },
        ),
    }

    ui_virtual_fields: ClassVar[dict[str, dict[str, Any]]] = {
        "items_table": {
            "title": "Collection Items",
        },
        "collection_relationships": {
            "title": "Collection Relationships",
            "description": "Visual representation of this collection's relationships with other collections",
        },
    }

    ui_table_of_contents: ClassVar[list[dict[str, str]]] = []

    @model_validator(mode="before")
    @classmethod
    def check_ids(cls, values):
        if not any(values.get(k) is not None for k in ("collection_id", "immutable_id")):
            raise ValueError("Collection must have at least collection_id or immutable_id")

        return values
