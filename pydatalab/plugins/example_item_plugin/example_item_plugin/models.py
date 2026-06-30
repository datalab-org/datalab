"""Example custom item types registered via this package's ``pydatalab.item_types``
entry points. Two linked ``Sample`` subtypes:

- ``Solution``: a single solute at a given concentration in a solvent; rendered by
  datalab's core ``CustomFieldsPanel`` (no JavaScript).
- ``MixedSolution``: blended from ``Solution`` items by volume. Its panel
  (``MixedSolutionPanel.vue``) pulls each solution's concentration and computes the
  resulting per-solute concentrations and total volume.
"""

from typing import Literal

from pydantic import ConfigDict, Field

from pydatalab.models.samples import Sample
from pydatalab.models.utils import BaseModel, EntryReference

# solute/solvent reference a starting material or another sample.
_SUBSTANCE_REF_TYPES = ["starting_materials", "samples"]


class Solution(Sample):
    """A solution of a single solute at a stated concentration, rendered with no plugin JS."""

    model_config = ConfigDict(
        title="Solution",
        json_schema_extra={
            "datalab_ui_color": "#3a7ca5",
            "datalab_ui_hidden_fields": ["synthesis_information"],
            "datalab_section_title": "Solution",
        },
    )

    type: Literal["solutions"] = "solutions"  # type: ignore[assignment]

    solute: EntryReference | None = Field(
        None, json_schema_extra={"datalab_ref_types": _SUBSTANCE_REF_TYPES}
    )

    concentration: float | None = Field(
        None,
        ge=0,
        json_schema_extra={
            "datalab_include_field_in_summary": True,
            "datalab_units": ["mol/L", "mmol/L"],
            "datalab_default_unit": "mol/L",
            "datalab_unit_field": "concentration_unit",
        },
    )
    concentration_unit: Literal["mol/L", "mmol/L"] = Field(
        "mol/L", json_schema_extra={"datalab_hidden": True}
    )

    solvent: EntryReference | None = Field(
        None, json_schema_extra={"datalab_ref_types": _SUBSTANCE_REF_TYPES}
    )


class MixtureComponent(BaseModel):
    """A volume of one :class:`Solution` taken into a :class:`MixedSolution`."""

    solution: EntryReference | None = None
    volume: float | None = None
    """Volume taken, in mL."""


class MixedSolution(Sample):
    """A solution blended from one or more :class:`Solution` items by volume, rendered by
    ``MixedSolutionPanel.vue`` (which pulls each solution's concentration and computes the
    resulting per-solute concentrations and total volume)."""

    model_config = ConfigDict(
        title="Mixed Solution", json_schema_extra={"datalab_ui_color": "#b5651d"}
    )

    type: Literal["mixed_solutions"] = "mixed_solutions"  # type: ignore[assignment]

    components: list[MixtureComponent] = Field(default_factory=list)
