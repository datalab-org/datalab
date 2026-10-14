<template>
  <div>
    <table v-if="!groupFields.length" class="table table-sm table-hover mb-2">
      <thead>
        <tr>
          <th scope="col"></th>
          <th v-for="col in effectiveColumns" :key="col.field" scope="col">{{ col.header }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in items" :key="rowKey(row)" role="button" @click="onRowClick(row)">
          <td>
            <input
              type="checkbox"
              :checked="isSelected(row)"
              aria-label="Select row"
              @click.stop="toggleSelected(row)"
            />
          </td>
          <td v-for="col in effectiveColumns" :key="col.field">{{ cellValue(row, col) }}</td>
        </tr>
        <tr v-if="!items.length">
          <td :colspan="effectiveColumns.length + 1" class="text-muted">No items</td>
        </tr>
      </tbody>
    </table>

    <div v-else class="list-group mb-2">
      <template v-for="bucket in buckets" :key="bucket.key">
        <button
          type="button"
          class="list-group-item list-group-item-action font-weight-bold"
          :aria-expanded="isExpanded(bucket.key)"
          @click="toggle(bucket.key)"
        >
          <font-awesome-icon
            :icon="isExpanded(bucket.key) ? 'chevron-down' : 'chevron-right'"
            class="mr-2"
          />
          {{ bucket.label }}
          <span class="badge badge-secondary badge-pill ml-1">{{ bucket.items.length }}</span>
        </button>
        <div v-if="isExpanded(bucket.key)" class="list-group-item pl-4">
          <GroupedDataTable
            :items="bucket.items"
            :group-fields="groupFields.slice(1)"
            :items-selected="itemsSelected"
            :columns="columns"
            @update:items-selected="$emit('update:items-selected', $event)"
            @row-click="$emit('row-click', $event)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { rowKey } from "@/utils/tableColumns.js";

const FALLBACK_COLUMNS = [
  { field: "item_id", header: "ID" },
  { field: "name", header: "Name" },
  { field: "status", header: "Status" },
  { field: "date", header: "Date" },
];

export default {
  name: "GroupedDataTable",
  props: {
    items: { type: Array, required: true },
    groupFields: { type: Array, required: true },
    itemsSelected: { type: Array, required: true },
    columns: { type: Array, default: () => [] },
  },
  emits: ["update:items-selected", "row-click"],
  data() {
    return {
      expanded: new Set(),
    };
  },
  computed: {
    effectiveColumns() {
      const withHeaders = this.columns.filter((c) => c.field && c.header);
      return withHeaders.length ? withHeaders : FALLBACK_COLUMNS;
    },
    buckets() {
      const field = this.groupFields[0];
      const map = new Map();
      for (const item of this.items) {
        for (const { key, label } of this.getGroupValues(item, field)) {
          if (!map.has(key)) {
            map.set(key, { key, label, items: [] });
          }
          map.get(key).items.push(item);
        }
      }
      const buckets = [...map.values()];
      const isEmpty = (b) => b.key === "__none__";
      return buckets.sort((a, b) => {
        // The group without a value goes last.
        if (isEmpty(a) !== isEmpty(b)) return isEmpty(a) ? 1 : -1;
        // Date keys sort chronologically as strings (YYYY, YYYY-MM, YYYY-MM-DD); newest first.
        if (field.id === "date") return b.key.localeCompare(a.key);
        return a.label.localeCompare(b.label);
      });
    },
  },
  methods: {
    rowKey,
    isSelected(row) {
      return this.itemsSelected.some((r) => this.rowKey(r) === this.rowKey(row));
    },
    toggleSelected(row) {
      const next = this.isSelected(row)
        ? this.itemsSelected.filter((r) => this.rowKey(r) !== this.rowKey(row))
        : [...this.itemsSelected, row];
      this.$emit("update:items-selected", next);
    },
    onRowClick(row) {
      this.$emit("row-click", row);
    },
    isExpanded(key) {
      return this.expanded.has(key);
    },
    toggle(key) {
      const next = new Set(this.expanded);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      this.expanded = next;
    },
    formatDate(value) {
      const d = new Date(value);
      return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString();
    },
    cellValue(row, col) {
      const value = row[col.field];
      if (value === undefined || value === null || value === "") return "";
      if (Array.isArray(value)) {
        if (value.length && typeof value[0] === "object") {
          return value
            .map((v) => v.display_name || v.collection_id || v.title || v.name)
            .filter(Boolean)
            .join(", ");
        }
        return String(value.length);
      }
      if (typeof value === "object") {
        return value.display_name || value.title || "";
      }
      if (["date", "date_opened", "last_modified"].includes(col.field)) {
        return this.formatDate(value);
      }
      return String(value);
    },
    getGroupValues(item, field) {
      if (field.id === "status") {
        const value = item.status;
        return [{ key: value || "__none__", label: value || "No status" }];
      }
      if (field.id === "creators") {
        const creators = item.creators || [];
        if (!creators.length) return [{ key: "__none__", label: "No creator" }];
        return creators.map((c) => ({
          key: c.display_name || "__none__",
          label: c.display_name || "No creator",
        }));
      }
      if (field.id === "date") {
        return [this.getDateBucket(item.date, field.grain || "month")];
      }
      if (field.id === "tags") {
        // Like creators, an item with several tags appears under each of them.
        const tags = (item.tags || []).filter((t) => t && (t.immutable_id || t.name));
        if (!tags.length) return [{ key: "__none__", label: "No tags" }];
        return tags.map((t) => ({ key: t.immutable_id || t.name, label: t.name || "Unnamed tag" }));
      }
      const value = item[field.id];
      if (value === undefined || value === null || value === "") {
        return [{ key: "__none__", label: "No value" }];
      }
      return [{ key: String(value), label: String(value) }];
    },
    getDateBucket(value, grain) {
      // Use the calendar date as stored (and as the Date column shows it: the first 10
      // characters), not the browser's local date, so that grouping matches the table.
      const match = typeof value === "string" ? value.match(/^(\d{4})-(\d{2})-(\d{2})/) : null;
      if (!match) {
        return { key: "__none__", label: "No date" };
      }
      const [y, m, d] = match.slice(1).map(Number);
      const day = new Date(Date.UTC(y, m - 1, d));
      const pad = (n) => String(n).padStart(2, "0");
      const isoDay = (date) =>
        `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
      const format = (date, options) =>
        date.toLocaleDateString(undefined, { ...options, timeZone: "UTC" });
      if (grain === "day") {
        return { key: isoDay(day), label: format(day) };
      }
      if (grain === "week") {
        const firstDay = new Date(Date.UTC(y, m - 1, d - day.getUTCDay()));
        return { key: isoDay(firstDay), label: `Week of ${format(firstDay)}` };
      }
      if (grain === "year") {
        return { key: `${y}`, label: `${y}` };
      }
      return {
        key: `${y}-${pad(m)}`,
        label: format(day, { month: "long", year: "numeric" }),
      };
    },
  },
};
</script>
