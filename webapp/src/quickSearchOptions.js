// Quick filters and group-by fields of the advanced search menu. Each only applies to tables
// that show one of its `columns`, i.e. whose rows carry the data it reads.
//
// Quick filters are presets of the advanced search: `filter()` gives an OPTIMADE filter and
// `params` extra parameters of the search request, so they run on the server with any
// custom filter, rather than being matched against the table's rows.

import { toRfc3339 } from "@/utils/optimadeFilter.js";

const CREATOR_COLUMNS = ["creatorsAndGroups", "creators"];
const DAY_MS = 24 * 60 * 60 * 1000;

const createdInLastDays = (days) => () =>
  `date >= "${toRfc3339(new Date(Date.now() - days * DAY_MS))}"`;

export const QUICK_FILTERS = [
  { id: "my_items", label: "My items", columns: CREATOR_COLUMNS, params: { mine: true } },
  {
    id: "latest_week",
    label: "Latest items (past week)",
    columns: ["date"],
    filter: createdInLastDays(7),
  },
  {
    id: "latest_month",
    label: "Latest items (past month)",
    columns: ["date"],
    filter: createdInLastDays(30),
  },
  {
    id: "active",
    label: "Active",
    columns: ["status"],
    // The "in use" status of each item type: samples and cells, equipment, starting materials.
    filter: () => 'status = "active" OR status = "working" OR status = "available"',
  },
  {
    id: "has_blocks",
    label: "Have blocks",
    columns: ["blocks"],
    filter: () => "NOT display_order LENGTH 0",
  },
];

export const STATIC_GROUP_FIELDS = [
  { id: "type", label: "Type", columns: ["type"] },
  { id: "creators", label: "Creators", columns: CREATOR_COLUMNS },
  { id: "status", label: "Status", columns: ["status"] },
  { id: "date", label: "Date", columns: ["date"] },
  { id: "tags", label: "Tags", columns: ["tags"] },
];
