/**
 * Row grouping for `DynamicDataTable`, used with PrimeVue's `rowGroupMode="subheader"`.
 *
 * Every row belongs to exactly one group, so that selection, sorting and the paginator keep
 * working on the table's own rows: an item with several tags (or creators) is grouped under
 * that combination of tags rather than repeated under each of them. Grouping by several
 * fields groups by the combination of their values.
 */

const NO_VALUE = { key: "", label: null };

function dateValue(value, grain) {
  // Use the calendar date as stored (and as the Date column shows it), not the browser's
  // local date, so that grouping matches the table.
  const match = typeof value === "string" ? value.match(/^(\d{4})-(\d{2})-(\d{2})/) : null;
  if (!match) return NO_VALUE;
  const [y, m, d] = match.slice(1).map(Number);
  const day = new Date(Date.UTC(y, m - 1, d));
  const pad = (n) => String(n).padStart(2, "0");
  const isoDay = (date) =>
    `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
  const format = (date, options) =>
    date.toLocaleDateString(undefined, { ...options, timeZone: "UTC" });

  if (grain === "day") return { key: isoDay(day), label: format(day) };
  if (grain === "week") {
    const firstDay = new Date(Date.UTC(y, m - 1, d - day.getUTCDay()));
    return { key: isoDay(firstDay), label: `Week of ${format(firstDay)}` };
  }
  if (grain === "year") return { key: `${y}`, label: `${y}` };
  return { key: `${y}-${pad(m)}`, label: format(day, { month: "long", year: "numeric" }) };
}

function listValue(names) {
  const sorted = [...new Set(names.filter(Boolean))].sort((a, b) => a.localeCompare(b));
  return sorted.length ? { key: sorted.join("\n"), label: sorted.join(", ") } : NO_VALUE;
}

/** The group a row falls in for one group-by field, as `{ key, label }`. */
export function groupValue(row, field) {
  if (field.id === "date") return dateValue(row.date, field.grain || "month");
  if (field.id === "tags") return listValue((row.tags || []).map((tag) => tag?.name));
  if (field.id === "creators") {
    const creators = row.creatorsAndGroups
      ? row.creatorsAndGroups.filter((entry) => entry.type === "creator")
      : row.creators || [];
    return listValue(creators.map((creator) => creator?.display_name));
  }
  const value = row[field.id];
  if (value === undefined || value === null || value === "") return NO_VALUE;
  return { key: String(value), label: String(value) };
}

/**
 * The grouping of a table by `fields`: `groupKey` maps a row to the key of its group (which
 * also sorts the groups, rows without a value last) and `labelOf` maps that key back to the
 * label shown in the group header.
 */
export function createRowGrouping(fields) {
  const labels = new Map();
  const groupKey = (row) => {
    const values = fields.map((field) => groupValue(row, field));
    // Prefixing each part keeps rows without a value after all the others.
    const key = values.map(({ key }) => (key ? `0${key}` : "1")).join("\u0000");
    if (!labels.has(key)) {
      labels.set(
        key,
        values.map(({ label }, i) => label ?? `No ${fields[i].label.toLowerCase()}`).join(" › "),
      );
    }
    return key;
  };
  return { groupKey, labelOf: (key) => labels.get(key) };
}

/** The number of rows in each group, keyed by group key. */
export function countGroups(rows, groupKey) {
  const counts = new Map();
  for (const row of rows || []) {
    const key = groupKey(row);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return counts;
}
