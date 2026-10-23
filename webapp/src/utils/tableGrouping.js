/**
 * Row grouping for `DynamicDataTable`: rows are grouped into a tree of collapsible groups, one
 * level per group-by field, which the table shows as group header rows within the DataTable.
 *
 * An item with several values for a field (tags, creators) is listed in the group of each of
 * them; group counts are numbers of distinct rows.
 */

import { FilterMatchMode, FilterOperator, FilterService } from "@primevue/core/api";

import { rowKey } from "@/utils/tableColumns.js";

const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function dateValue(value, grain) {
  // Use the calendar date as stored (and as the Date column shows it), not the browser's
  // local date, so that grouping matches the table.
  const match = typeof value === "string" ? value.match(/^(\d{4})-(\d{2})-(\d{2})/) : null;
  if (!match) return [];
  const [y, m, d] = match.slice(1).map(Number);
  const day = new Date(Date.UTC(y, m - 1, d));
  const pad = (n) => String(n).padStart(2, "0");
  const isoDay = (date) =>
    `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
  const format = (date, options) =>
    date.toLocaleDateString(undefined, { ...options, timeZone: "UTC" });

  if (grain === "day") return [{ key: isoDay(day), label: format(day) }];
  if (grain === "week") {
    const firstDay = new Date(Date.UTC(y, m - 1, d - day.getUTCDay()));
    return [{ key: isoDay(firstDay), label: `Week of ${format(firstDay)}` }];
  }
  if (grain === "year") return [{ key: `${y}`, label: `${y}` }];
  return [{ key: `${y}-${pad(m)}`, label: format(day, { month: "long", year: "numeric" }) }];
}

function namedValues(names) {
  return [...new Set(names.filter(Boolean))].map((name) => ({ key: name, label: name }));
}

/** The groups a row belongs to for one group-by field, as `{ key, label }`; none if empty. */
export function groupValues(row, field) {
  if (field.id === "date") return dateValue(row.date, field.grain || "month");
  if (field.id === "tags") return namedValues((row.tags || []).map((tag) => tag?.name));
  if (field.id === "creators") {
    const creators = row.creatorsAndGroups
      ? row.creatorsAndGroups.filter((entry) => entry.type === "creator")
      : row.creators || [];
    return namedValues(creators.map((creator) => creator?.display_name));
  }
  const value = row[field.id];
  if (value === undefined || value === null || value === "") return [];
  return [{ key: String(value), label: String(value) }];
}

/**
 * The tree of groups of `rows` by `fields`: each group has a unique `key`, its `label`, the
 * `count` of its rows, its `rows` and, but for the last field, its `children` groups.
 * Groups are sorted by value, with the group of rows without a value last.
 */
export function buildGroupTree(rows, fields, depth = 0, parent = null) {
  const field = fields[depth];
  const groups = new Map();
  for (const row of rows) {
    const values = groupValues(row, field);
    for (const { key, label } of values.length ? values : [{ key: null, label: null }]) {
      if (!groups.has(key)) groups.set(key, { key, label, rows: [] });
      groups.get(key).rows.push(row);
    }
  }
  return [...groups.values()]
    .sort((a, b) => (a.key === null) - (b.key === null) || collator.compare(a.key, b.key))
    .map(({ key, label, rows: groupRows }) => {
      const group = {
        key: `${parent ? parent.key : ""}\u0000${key ?? ""}`,
        label: label ?? `No ${field.label.toLowerCase()}`,
        depth,
        parent,
        count: groupRows.length,
        rows: groupRows,
      };
      group.children =
        depth + 1 < fields.length ? buildGroupTree(groupRows, fields, depth + 1, group) : [];
      return group;
    });
}

function headerEntry(group) {
  return { group, __groupKey: group.key };
}

/**
 * The rows the table shows for `groups`: a header row for each group, followed, when it is in
 * `expandedKeys`, by its subgroups or its rows. A row listed in several groups is a copy of
 * the table's row, which keeps the original as `__row`.
 */
export function flattenGroups(groups, expandedKeys, entries = []) {
  for (const group of groups) {
    entries.push(headerEntry(group));
    if (!expandedKeys.has(group.key)) continue;
    if (group.children.length) {
      flattenGroups(group.children, expandedKeys, entries);
    } else {
      for (const row of group.rows) {
        entries.push({ ...row, __groupKey: group.key, __row: row });
      }
    }
  }
  return entries;
}

/** The rows of the table shown in `entries`, each once. */
export function rowsOfEntries(entries) {
  return [...new Set(entries.filter((entry) => entry.__row).map((entry) => entry.__row))];
}

function fieldValue(row, field) {
  return field.split(".").reduce((value, key) => (value == null ? value : value[key]), row);
}

function isEmpty(value) {
  return (
    value === null || value === undefined || value === "" || (Array.isArray(value) && !value.length)
  );
}

/**
 * The rows matching a DataTable `filters` model, as DataTable itself filters them: grouped
 * tables filter their rows before grouping them, as their DataTable only shows the groups.
 */
export function filterRows(rows, filters, globalFilterFields = []) {
  const columnFilters = Object.entries(filters || {})
    .filter(([field]) => field !== "global")
    .map(([field, meta]) => [
      field,
      meta,
      (meta.constraints || []).filter((c) => !isEmpty(c.value)),
    ])
    .filter(([, , constraints]) => constraints.length);
  const globalValue = filters?.global?.value;

  return rows.filter((row) => {
    const matchesColumns = columnFilters.every(([field, meta, constraints]) => {
      const results = constraints.map((constraint) =>
        FilterService.filters[constraint.matchMode || FilterMatchMode.STARTS_WITH](
          fieldValue(row, field),
          constraint.value,
        ),
      );
      return meta.operator === FilterOperator.OR ? results.some(Boolean) : results.every(Boolean);
    });
    if (!matchesColumns || isEmpty(globalValue)) return matchesColumns;
    return globalFilterFields.some((field) =>
      FilterService.filters[FilterMatchMode.CONTAINS](fieldValue(row, field), globalValue),
    );
  });
}

/** `rows` sorted by a DataTable `multiSortMeta`, keeping their order otherwise. */
export function sortRows(rows, multiSortMeta = []) {
  if (!multiSortMeta?.length) return rows;
  return [...rows].sort((a, b) => {
    for (const { field, order } of multiSortMeta) {
      const [x, y] = [fieldValue(a, field), fieldValue(b, field)];
      if (x === y) continue;
      if (x == null) return 1;
      if (y == null) return -1;
      const compared =
        typeof x === "number" && typeof y === "number" ? x - y : collator.compare(x, y);
      if (compared) return compared * order;
    }
    return 0;
  });
}

/** Whether a row is in `selection`, which holds the table's rows. */
export function isRowSelected(selection, row) {
  const key = rowKey(row);
  return selection.some((selected) => rowKey(selected) === key);
}

/** `selection` with `rows` added to it, or removed from it. */
export function setRowsSelected(selection, rows, selected) {
  const keys = new Set(rows.map(rowKey));
  const others = selection.filter((row) => !keys.has(rowKey(row)));
  return selected ? [...others, ...rows] : others;
}

/**
 * Groups `rows` by `fields` as a grouped table shows them: filtered and sorted first, as
 * DataTable does for ungrouped tables, since it only gets the grouped table's current page.
 * Returns the matching `rows`, the `entries` (group headers and rows) to show, and the
 * `groups` by key.
 */
export function groupRows(rows, fields, { filters, globalFilterFields, sortMeta, expandedKeys }) {
  const matching = sortRows(filterRows(rows, filters, globalFilterFields), sortMeta);
  const tree = buildGroupTree(matching, fields);
  const groups = new Map();
  const index = (nodes) =>
    nodes.forEach((group) => {
      groups.set(group.key, group);
      index(group.children);
    });
  index(tree);
  return { rows: matching, entries: flattenGroups(tree, expandedKeys), groups };
}
