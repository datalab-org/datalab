// Quick filters and group-by fields of the advanced search menu. Each only applies to tables
// that show one of its `columns`, i.e. whose rows carry the data it reads.

const CREATOR_COLUMNS = ["creatorsAndGroups", "creators"];

export const QUICK_FILTERS = [
  { id: "my_items", label: "My items", columns: CREATOR_COLUMNS },
  { id: "latest_week", label: "Latest items (past week)", columns: ["date"] },
  { id: "latest_month", label: "Latest items (past month)", columns: ["date"] },
  { id: "active", label: "Active", columns: ["status"] },
  { id: "has_blocks", label: "Have blocks", columns: ["blocks"] },
];

export const STATIC_GROUP_FIELDS = [
  { id: "type", label: "Type", columns: ["type"] },
  { id: "creators", label: "Creators", columns: CREATOR_COLUMNS },
  { id: "status", label: "Status", columns: ["status"] },
  { id: "date", label: "Date", columns: ["date"] },
  { id: "tags", label: "Tags", columns: ["tags"] },
];
