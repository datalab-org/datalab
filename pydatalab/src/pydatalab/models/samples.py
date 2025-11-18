from typing import ClassVar, Literal

from pydantic import Field

from pydatalab.models.items import Item
from pydatalab.models.traits import HasSynthesisInfo
from pydatalab.models.traits.ui_hints import HasUIHints, UIFieldConfig


class Sample(Item, HasSynthesisInfo, HasUIHints):
    """A model for representing an experimental sample."""

    type: Literal["samples"] = "samples"

    chemform: str | None = Field(
        None,
        examples=["Na3P", "LiNiO2@C"],
        title="Chemical Formula",
        description="A string representation of the chemical formula or composition associated with this sample.",
    )

    ui_layout: ClassVar[list[list[str]]] = [
        ["name", "chemform", "date"],
        ["refcode", "creators", "collections"],
        ["description"],
        ["table_of_contents"],
        ["synthesis_information"],
    ]

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {
        "name": UIFieldConfig(component="input", width="col-sm-4 pr-2 col-6"),
        "chemform": UIFieldConfig(component="ChemFormulaInput", width="col-sm-4 pr-2 col-6"),
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
            component="TableOfContents",
            width="col-12",
            hide_label=True,
            title="Table of Contents",
            component_props={
                "sections": [
                    {"title": "Sample Information", "targetID": "samples-information"},
                    {"title": "Table of Contents", "targetID": "table-of-contents"},
                    {"title": "Synthesis Information", "targetID": "synthesis-information"},
                ]
            },
        ),
        "synthesis_information": UIFieldConfig(
            component="SynthesisInformation",
            width="col-12",
            hide_label=True,
            title="Synthesis Information",
        ),
        "item_relationships": UIFieldConfig(
            component="ItemRelationshipVisualization",
            width="col-12",
            title="Item Relationships",
            description="Visual representation of this item's relationships with other items",
            hidden=True,
        ),
    }
