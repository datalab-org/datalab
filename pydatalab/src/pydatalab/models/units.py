"""Models describing unit conversions for numeric item fields."""

import math

from pydantic import ConfigDict, Field, field_validator, model_validator

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


class DatalabQuantity(BaseModel):
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
