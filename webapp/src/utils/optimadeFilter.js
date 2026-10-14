// Builds OPTIMADE filter strings from the advanced-search rule tree, following
// https://www.optimade.org/specification/latest/#api-filtering-format-specification

const NO_VALUE_OPERATORS = ["IS KNOWN", "IS UNKNOWN"];
const VALUE_LIST_OPERATORS = ["HAS ALL", "HAS ANY", "HAS ONLY"];

// String literals are double-quoted, with `"` and `\` as the only escaped characters.
export function quoteString(value) {
  return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

// Timestamps are compared as RFC 3339 strings; `datetime-local` inputs are in local time.
export function toRfc3339(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid date: ${value}`);
  }
  return date.toISOString().replace(/\.\d{3}Z$/, "Z");
}

function formatValue(value, valueType) {
  if (valueType === "number") {
    const number = Number(value);
    if (value === "" || value === null || !Number.isFinite(number)) {
      throw new Error(`Invalid number: ${value}`);
    }
    return String(number);
  }
  if (valueType === "timestamp") {
    return quoteString(toRfc3339(value));
  }
  return quoteString(value);
}

function asList(value) {
  return (Array.isArray(value) ? value : [value]).filter(
    (v) => v !== undefined && v !== null && v !== "",
  );
}

export function buildRuleFilter(rule, field) {
  const property = rule.field;
  const operator = rule.operator;
  const valueType = field?.value_type || "string";

  if (NO_VALUE_OPERATORS.includes(operator)) {
    return `${property} ${operator}`;
  }
  if (operator === "LENGTH") {
    return `${property} LENGTH ${formatValue(rule.value, "number")}`;
  }
  if (VALUE_LIST_OPERATORS.includes(operator)) {
    const values = asList(rule.value).map((v) => formatValue(v, valueType));
    return `${property} ${operator} ${values.join(", ")}`;
  }
  return `${property} ${operator} ${formatValue(rule.value, valueType)}`;
}

// Children are joined with the group's combinator; nested groups are always
// parenthesised so that the result does not depend on AND binding tighter than OR.
export function buildOptimadeFilter(node, fields = []) {
  if (!node) return "";
  if (node.kind === "rule") {
    return buildRuleFilter(
      node,
      fields.find((f) => f.id === node.field),
    );
  }

  const parts = (node.children || [])
    .map((child) => {
      const part = buildOptimadeFilter(child, fields);
      return part && child.kind === "group" ? `(${part})` : part;
    })
    .filter(Boolean);
  if (!parts.length) return "";

  const combinator = (node.combinator || "and").toUpperCase() === "OR" ? " OR " : " AND ";
  const joined = parts.join(combinator);
  if (!node.negate) return joined;
  return parts.length === 1 ? `NOT ${joined}` : `NOT (${joined})`;
}
