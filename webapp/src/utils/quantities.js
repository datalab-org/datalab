// This file was edited with the assistance of an AI model and requires human review from the contributor.

// Helpers for numeric fields that carry a `datalab_quantity` schema hint. Such a field is
// always stored in its canonical unit; other units are a display concern only, with
//
//   canonical = displayed * scale + offset
//

// Significant figures kept after a conversion, to trim floating-point noise
// (e.g. 5.1000000000000005).
const CONVERSION_PRECISION = 12;

function isNumeric(value) {
  return value !== null && value !== undefined && value !== "" && !Number.isNaN(Number(value));
}

// Resolve the `datalab_quantity` hint of a JSON schema property, or null if it has none.
export function resolveQuantity(propertySchema) {
  const extra = propertySchema?.["x-json_schema_extra"] || propertySchema;
  const config = extra?.datalab_quantity;
  if (!config) return null;

  const transforms = Object.fromEntries(
    Object.entries(config.display_units || {}).map(([unit, transform]) => [
      unit,
      { scale: transform.scale ?? 1, offset: transform.offset ?? 0 },
    ]),
  );
  // `display_units` may be omitted for a field only ever displayed in its canonical unit.
  if (Object.keys(transforms).length === 0) {
    transforms[config.canonical_unit] = { scale: 1, offset: 0 };
  }
  return {
    canonicalUnit: config.canonical_unit,
    units: Object.keys(transforms),
    transforms,
    defaultDisplayUnit: config.default_display_unit || config.canonical_unit,
    // Optional companion field persisting the display unit; when absent, the choice
    // of display unit is not stored with the item.
    displayUnitField: config.display_unit_field || null,
  };
}

// A quantity with only its canonical unit, for when no schema hint is available.
export function canonicalOnlyQuantity(unit) {
  return {
    canonicalUnit: unit,
    units: [unit],
    transforms: { [unit]: { scale: 1, offset: 0 } },
    defaultDisplayUnit: unit,
    displayUnitField: null,
  };
}

// Convert a canonical value for display in `unit`. Non-numeric values pass through.
export function toDisplayValue(quantity, unit, canonicalValue) {
  if (!isNumeric(canonicalValue)) return canonicalValue;
  const { scale, offset } = quantity.transforms[unit] || { scale: 1, offset: 0 };
  return Number(((Number(canonicalValue) - offset) / scale).toPrecision(CONVERSION_PRECISION));
}

// Convert a value displayed in `unit` back to the canonical unit. Non-numeric values
// pass through, so that invalid input can still be shown (and flagged) as typed.
export function fromDisplayValue(quantity, unit, displayedValue) {
  if (!isNumeric(displayedValue)) return displayedValue;
  const { scale, offset } = quantity.transforms[unit] || { scale: 1, offset: 0 };
  return Number((Number(displayedValue) * scale + offset).toPrecision(CONVERSION_PRECISION));
}
