"""Example custom item types contributed by an out-of-tree plugin package, registered
via the ``pydatalab.item_types`` entry points in this package's ``pyproject.toml``.

These examples cover both ways a custom type's fields are rendered in the web UI:

- ``ExampleSample`` / ``AnnealingProtocol`` are rendered **automatically from their schema
  annotations** by datalab's core ``CustomFieldsPanel`` — the plugin ships *no* JavaScript.
- ``HeatTreatment`` ships a **custom panel** (``HeatTreatmentPanel.vue``) that references
  another custom type (``AnnealingProtocol``), pulls its parameters via "Populate from
  protocol" (cf. the AELIOS "Populate from recipe" flow), and draws a live
  temperature-vs-time plot — none of which is expressible with annotations alone.

``AnnealingProtocol`` and ``HeatTreatment`` form a linked pair: a heat-treated sample points
at the reusable protocol it followed, demonstrating cross-custom-type references.
"""

from typing import Literal

from pydantic import ConfigDict, Field

from pydatalab.models.samples import Sample
from pydatalab.models.utils import EntryReference

Atmosphere = Literal["air", "N2", "Ar", "O2", "forming_gas", "vacuum"]


class ExampleSample(Sample):
    """A minimal custom Sample subtype contributed by an out-of-tree plugin package."""

    model_config = ConfigDict(
        title="Example Sample",
        json_schema_extra={
            "datalab_ui_hidden_fields": [
                "synthesis_information",
                "description",
            ]
        },
    )

    type: Literal["example_samples"] = "example_samples"  # type: ignore[assignment]

    voltage: float | None = Field(
        None,
        json_schema_extra={
            "datalab_include_field_in_summary": True,
            "units": ["mV", "V", "kV"],
            "default_unit": "V",
            "datalab_unit_field": "voltage_unit",
        },
    )
    """Voltage value; the companion field `voltage_unit` holds the selected unit."""

    voltage_unit: Literal["mV", "V", "kV"] = Field(
        "V",
        json_schema_extra={"datalab_hidden": True},
    )
    """Selected unit for the voltage field. Hidden from standalone rendering."""


class AnnealingProtocol(Sample):
    """Annotation-rendered example — a reusable heat-treatment schedule shown with **no plugin
    JavaScript**. Every field below is driven by ``json_schema_extra`` annotations that
    datalab's core ``CustomFieldsPanel`` already understands: an enum dropdown, an inline
    equipment reference, and three number-with-unit compound widgets. A ``HeatTreatment``
    item references one of these and pulls its parameters via "Populate from protocol"."""

    model_config = ConfigDict(
        title="Annealing Protocol",
        json_schema_extra={
            "datalab_ui_hidden_fields": ["synthesis_information", "substance_information"],
            "datalab_section_title": "Annealing Schedule",
            "datalab_ui_color": "#b5651d",
        },
    )

    type: Literal["annealing_protocols"] = "annealing_protocols"  # type: ignore[assignment]

    atmosphere: Atmosphere | None = Field(
        None,
        title="Atmosphere",
        json_schema_extra={"datalab_section": "Equipment & Safety"},
    )

    furnace: EntryReference | None = Field(
        None,
        description="The furnace this protocol is intended for.",
        json_schema_extra={
            "datalab_ref_types": ["equipment"],
            "datalab_section": "Equipment & Safety",
        },
    )
    """Inline item-reference widget (no JavaScript) pointing at a built-in ``equipment`` item."""

    peak_temperature: float | None = Field(
        None,
        ge=0,
        title="Peak temperature",
        json_schema_extra={
            "units": ["°C", "K"],
            "default_unit": "°C",
            "datalab_unit_field": "peak_temperature_unit",
            "datalab_include_field_in_summary": True,
        },
    )
    peak_temperature_unit: Literal["°C", "K"] = Field(
        "°C", json_schema_extra={"datalab_hidden": True}
    )

    ramp_rate: float | None = Field(
        None,
        ge=0,
        title="Ramp rate",
        json_schema_extra={
            "units": ["°C/min", "K/min"],
            "default_unit": "°C/min",
            "datalab_unit_field": "ramp_rate_unit",
        },
    )
    ramp_rate_unit: Literal["°C/min", "K/min"] = Field(
        "°C/min", json_schema_extra={"datalab_hidden": True}
    )

    dwell_time: float | None = Field(
        None,
        ge=0,
        title="Dwell time",
        json_schema_extra={
            "units": ["min", "h"],
            "default_unit": "min",
            "datalab_unit_field": "dwell_time_unit",
        },
    )
    dwell_time_unit: Literal["min", "h"] = Field("min", json_schema_extra={"datalab_hidden": True})

    # A second card: fields sharing a different ``datalab_section`` group into their own
    # panel — demonstrating that even an annotation-only type can have multiple sections.
    requires_supervision: bool | None = Field(
        None,
        title="Requires supervision",
        json_schema_extra={"datalab_section": "Equipment & Safety"},
    )
    hazard_notes: str | None = Field(
        None,
        title="Hazard notes",
        json_schema_extra={"datalab_section": "Equipment & Safety", "datalab_multiline": True},
    )


class HeatTreatment(Sample):
    """Custom-panel example — a sample that underwent a heat treatment, rendered by a bespoke
    ``HeatTreatmentPanel.vue``. It links to an ``AnnealingProtocol`` (a *custom* type),
    seeds its as-run schedule from that protocol ("Populate from protocol"), and the panel
    draws a live temperature-vs-time profile with computed peak and total duration."""

    model_config = ConfigDict(
        title="Heat-Treated Sample",
        json_schema_extra={
            "datalab_ui_hidden_fields": ["synthesis_information"],
            "datalab_ui_color": "#a83232",
        },
    )

    type: Literal["heat_treatments"] = "heat_treatments"  # type: ignore[assignment]

    protocol: EntryReference | None = Field(
        None, description="The annealing protocol applied (a custom item type)."
    )
    precursor: EntryReference | None = Field(
        None, description="The precursor material that was heat-treated."
    )

    atmosphere: Atmosphere | None = Field(None, title="Atmosphere")

    # As-run schedule in normalized units (°C, °C/min, min). Seeded from the linked
    # protocol by the panel and then editable. Rendered entirely by the bespoke .vue.
    peak_temperature: float | None = Field(None, ge=0, description="As-run peak temperature (°C).")
    ramp_rate: float | None = Field(None, ge=0, description="As-run ramp rate (°C/min).")
    dwell_time: float | None = Field(None, ge=0, description="As-run dwell time (min).")

    # Characterization — rendered as a SECOND card by the bespoke panel, next to a
    # client-computed mass-loss bar.
    resulting_phase: (
        Literal["olivine", "spinel", "layered", "rock-salt", "perovskite", "amorphous", "other"]
        | None
    ) = Field(None, description="Phase identified after treatment.")
    mass_before: float | None = Field(None, ge=0, description="Mass before treatment (g).")
    mass_after: float | None = Field(None, ge=0, description="Mass after treatment (g).")
    color: str | None = Field(None, description="Observed colour of the product.")
    crucible: Literal["alumina", "platinum", "quartz", "graphite"] | None = Field(
        None, description="Crucible material used."
    )
