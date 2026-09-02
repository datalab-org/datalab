"""Typed definitions of the ``datalab_*`` ``json_schema_extra`` hints.

Item models tag fields and model config with ``datalab_*`` keys that the API and
web UI read back (summary projection, field rendering, grouping, ...). The two
models below list the valid keys; :func:`validate_schema_hints` checks them at
registration, and ``invoke dev.generate-schemas`` exports them as JSON schemas.

Call sites keep writing plain dicts. The field names here match the literal keys,
and the attribute docstrings become the descriptions in the generated schema.
"""

import math

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from pydatalab.models.utils import BaseModel


class DatalabUnitTransform(BaseModel):
    """Affine conversion from a display unit to a field's canonical unit."""

    model_config = ConfigDict(extra="forbid")

    scale: float = 1.0
    """Multiplier in ``canonical = displayed * scale + offset``."""

    offset: float = 0.0
    """Offset in ``canonical = displayed * scale + offset``."""

    @field_validator("scale")
    @classmethod
    def _valid_scale(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("scale must be positive and finite")
        return value

    @field_validator("offset")
    @classmethod
    def _valid_offset(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("offset must be finite")
        return value


class DatalabQuantityExtra(BaseModel):
    """Canonical storage and display-unit configuration for a numeric field."""

    model_config = ConfigDict(extra="forbid")

    canonical_unit: str = Field(min_length=1)
    """Unit used by the Pydantic field, REST API, application state, and database."""

    display_units: dict[str, DatalabUnitTransform]
    """Allowed display units and their affine transforms to the canonical unit."""

    default_display_unit: str | None = None
    """Initial display unit; defaults to ``canonical_unit`` when omitted."""

    display_unit_field: str | None = None
    """Optional companion field that persists presentation preference only."""

    @model_validator(mode="after")
    def _valid_quantity(self):
        if not self.display_units:
            raise ValueError("display_units must contain at least the canonical unit")

        if any(not unit for unit in self.display_units):
            raise ValueError("display unit names must not be empty")

        if self.canonical_unit not in self.display_units:
            raise ValueError("canonical_unit must be present in display_units")

        canonical = self.display_units[self.canonical_unit]
        if canonical.scale != 1.0 or canonical.offset != 0.0:
            raise ValueError("the canonical unit must use the identity transform")

        if (
            self.default_display_unit is not None
            and self.default_display_unit not in self.display_units
        ):
            raise ValueError("default_display_unit must be present in display_units")

        return self


class DatalabFieldExtra(BaseModel):
    """Datalab hints attached to a field via ``json_schema_extra``."""

    model_config = ConfigDict(extra="forbid")

    datalab_include_field_in_summary: bool | None = None
    """Also show this field in list/summary views."""

    datalab_hidden: bool | None = None
    """Store but don't render this field directly."""

    datalab_multiline: bool | None = None
    """Render a string as a multi-line textarea."""

    datalab_section: str | None = None
    """Group fields sharing this section string into their own card."""

    datalab_ref_types: list[str] | None = None
    """Render an item-reference widget restricted to these item types."""

    datalab_quantity: DatalabQuantityExtra | None = None
    """Render a canonical numeric field with plugin-defined display-unit conversions."""

    datalab_exclude_from_db: bool | None = None
    """Don't persist this field to the database (block models)."""

    datalab_exclude_from_load: bool | None = None
    """Don't populate this field when loading from the database (block models)."""


class DatalabModelExtra(BaseModel):
    """Datalab hints attached to a model via ``model_config['json_schema_extra']``."""

    model_config = ConfigDict(extra="forbid")

    datalab_ui_hidden_fields: list[str] | None = None
    """Inherited field names to hide from the UI for this item type."""

    datalab_ui_color: str | None = None
    """Accent colour (CSS hex) used for this item type in the UI."""

    datalab_section_title: str | None = None
    """Title of the default custom-fields card."""

    datalab_base_type: str | None = None
    """Built-in type this derives from, when not inferable from the class hierarchy."""


def _datalab_hint_keys(extra: dict) -> dict:
    """Pick the ``datalab_*`` hint keys out of a raw ``json_schema_extra`` dict.

    Only ``datalab_*`` keys are returned, so legitimate standard JSON Schema keys
    (e.g. ``format``) declared in the same dict are left untouched.
    """
    return {k: v for k, v in extra.items() if k.startswith("datalab_")}


def _non_null_schema_types(schema: dict) -> set[str]:
    """Return JSON Schema primitive types, ignoring nullable branches."""
    types: set[str] = set()
    if isinstance(schema.get("type"), str) and schema["type"] != "null":
        types.add(schema["type"])
    for branch in schema.get("anyOf", []):
        if isinstance(branch, dict):
            types.update(_non_null_schema_types(branch))
    return types


def _schema_enum_values(schema: dict) -> set[str] | None:
    """Return string enum values from a direct or nullable JSON Schema."""
    enum = schema.get("enum")
    if isinstance(enum, list) and all(isinstance(value, str) for value in enum):
        return set(enum)
    for branch in schema.get("anyOf", []):
        if isinstance(branch, dict):
            values = _schema_enum_values(branch)
            if values is not None:
                return values
    return None


def validate_schema_hints(model: type[BaseModel]) -> None:
    """Validate the datalab ``json_schema_extra`` hints on ``model`` and its fields.

    Checks the model-level config extras against :class:`DatalabModelExtra` and
    each field's extras against :class:`DatalabFieldExtra`, raising ``ValueError``
    that names the offending type/field if an unknown or mistyped ``datalab_*``
    hint is found. Non-datalab keys are ignored.
    """
    name = getattr(model, "__name__", str(model))

    model_extra = model.model_config.get("json_schema_extra")
    if isinstance(model_extra, dict):
        try:
            DatalabModelExtra(**_datalab_hint_keys(model_extra))
        except ValidationError as exc:
            raise ValueError(f"Invalid datalab model schema hints on {name!r}: {exc}") from exc

    schema_properties = model.model_json_schema(by_alias=False).get("properties", {})

    claimed_display_unit_fields: dict[str, str] = {}

    for field_name, field in model.model_fields.items():
        field_extra = field.json_schema_extra
        if not isinstance(field_extra, dict):
            continue
        try:
            parsed = DatalabFieldExtra(**_datalab_hint_keys(field_extra))
        except ValidationError as exc:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: {exc}"
            ) from exc

        quantity = parsed.datalab_quantity
        if quantity is None:
            continue

        field_schema = schema_properties.get(field_name, {})
        if _non_null_schema_types(field_schema) != {"number"}:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: "
                "datalab_quantity requires a floating-point field"
            )

        display_unit_field = quantity.display_unit_field
        if display_unit_field is None:
            continue
        if display_unit_field == field_name or display_unit_field not in model.model_fields:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: "
                f"display_unit_field {display_unit_field!r} does not name another model field"
            )

        existing_owner = claimed_display_unit_fields.get(display_unit_field)
        if existing_owner is not None:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: "
                f"display_unit_field {display_unit_field!r} is already used by {existing_owner!r}"
            )
        claimed_display_unit_fields[display_unit_field] = field_name

        unit_schema = schema_properties.get(display_unit_field, {})
        unit_values = _schema_enum_values(unit_schema)
        expected_values = set(quantity.display_units)
        if unit_values != expected_values:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: "
                f"display_unit_field {display_unit_field!r} must be a string Literal "
                f"containing exactly {sorted(expected_values)!r}"
            )

        unit_default = model.model_fields[display_unit_field].default
        if unit_default is not None and unit_default not in expected_values:
            raise ValueError(
                f"Invalid datalab schema hints on {name!r}.{field_name!r}: "
                f"the default for display_unit_field {display_unit_field!r} is not allowed"
            )
