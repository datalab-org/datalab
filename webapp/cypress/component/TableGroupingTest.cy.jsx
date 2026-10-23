import DynamicDataTable from "@/components/DynamicDataTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";
import { ITEM_ID_COLUMN, STATUS_COLUMN } from "@/utils/tableColumns.js";
import {
  buildGroupTree,
  filterRows,
  flattenGroups,
  groupValues,
  setRowsSelected,
  sortRows,
} from "@/utils/tableGrouping.js";

const tag = (name) => ({ type: "tags", immutable_id: name, name });

describe("tableGrouping", () => {
  it("lists an item in the group of each of its tags", () => {
    const rows = [
      { item_id: "a", tags: [tag("red"), tag("blue")] },
      { item_id: "b", tags: [tag("blue")] },
      { item_id: "c", tags: [] },
    ];
    const tree = buildGroupTree(rows, [{ id: "tags", label: "Tags" }]);
    expect(tree.map((g) => [g.label, g.count])).to.deep.equal([
      ["blue", 2],
      ["red", 1],
      ["No tags", 1],
    ]);
  });

  it("nests groups, one level per field", () => {
    const rows = [
      { item_id: "a", type: "samples", status: "active" },
      { item_id: "b", type: "samples", status: "planned" },
      { item_id: "c", type: "cells" },
    ];
    const tree = buildGroupTree(rows, [
      { id: "type", label: "Type" },
      { id: "status", label: "Status" },
    ]);
    expect(tree.map((g) => g.label)).to.deep.equal(["cells", "samples"]);
    expect(tree[0].children.map((g) => g.label)).to.deep.equal(["No status"]);
    expect(tree[1].children.map((g) => [g.label, g.depth, g.parent.label])).to.deep.equal([
      ["active", 1, "samples"],
      ["planned", 1, "samples"],
    ]);
  });

  it("only lists the rows of expanded groups", () => {
    const rows = [{ item_id: "a", status: "active" }];
    const tree = buildGroupTree(rows, [{ id: "status", label: "Status" }]);
    expect(flattenGroups(tree, new Set())).to.have.length(1);
    const entries = flattenGroups(tree, new Set([tree[0].key]));
    expect(entries.map((entry) => entry.group?.label ?? entry.__row.item_id)).to.deep.equal([
      "active",
      "a",
    ]);
  });

  it("groups dates by the stored calendar month", () => {
    const [value] = groupValues({ date: "2026-01-31T23:30:00" }, { id: "date", grain: "month" });
    expect(value.key).to.equal("2026-01");
  });

  it("filters and sorts rows as DataTable does", () => {
    const rows = [{ item_id: "b1" }, { item_id: "a1" }, { item_id: "c2" }];
    const filters = {
      global: { value: "1" },
      item_id: { operator: "and", constraints: [{ value: null, matchMode: "contains" }] },
    };
    const matching = filterRows(rows, filters, ["item_id"]);
    expect(
      sortRows(matching, [{ field: "item_id", order: -1 }]).map((r) => r.item_id),
    ).to.deep.equal(["b1", "a1"]);
  });

  it("selects a row once whatever group it is selected from", () => {
    const row = { item_id: "a" };
    const selection = setRowsSelected(setRowsSelected([], [row], true), [row], true);
    expect(selection).to.deep.equal([row]);
    expect(setRowsSelected(selection, [row], false)).to.deep.equal([]);
  });
});

describe("DynamicDataTable grouping", () => {
  let table;
  // 25 rows: 15 active, 10 planned; the first is also tagged "red" and "blue".
  const rows = Array.from({ length: 25 }, (_, i) => ({
    item_id: `s${String(i).padStart(2, "0")}`,
    type: "samples",
    status: i % 5 < 3 ? "active" : "planned",
    tags: i === 0 ? [tag("red"), tag("blue")] : [],
  }));

  const visibleRows = () =>
    cy.get(".p-datatable-tbody > tr").then((trs) =>
      [...trs]
        .filter((tr) => getComputedStyle(tr).display !== "none")
        .map((tr) => {
          const header = tr.querySelector('[data-testid="group-header"]');
          return header
            ? `# ${header.textContent.replace(/\s+/g, " ").trim()}`
            : tr.cells[1].innerText.trim();
        }),
    );
  const header = (label) => cy.contains('[data-testid="group-header"]', label);

  beforeEach(() => {
    localStorage.clear();
    const store = createStore({
      state() {
        return {
          currentUserID: "self",
          datatablePaginationSettings: { samples: { page: 0, rows: 20 } },
        };
      },
      getters: { isAdminSuperUserModeActive: () => false },
      mutations: {
        setPage(state, { type, page }) {
          state.datatablePaginationSettings[type].page = page;
        },
        setRows(state, { type, rows }) {
          state.datatablePaginationSettings[type].rows = rows;
        },
      },
    });
    cy.mount(DynamicDataTable, {
      props: {
        columns: [ITEM_ID_COLUMN, STATUS_COLUMN],
        data: rows,
        dataType: "samples",
        globalFilterFields: ["item_id"],
      },
      global: { plugins: [store, PrimeVue] },
    }).then(({ wrapper }) => {
      table = wrapper.vm;
    });
  });

  const groupBy = (fields) =>
    cy.then(() => {
      table.groupByFields = fields;
      return table.$nextTick();
    });

  it("shows collapsed groups inside the table, which open on click", () => {
    groupBy([{ id: "status", label: "Status" }]);
    visibleRows().should("deep.equal", ["# active 15", "# planned 10"]);
    cy.get(".p-datatable-thead th").should("contain.text", "Status");

    header("planned").click();
    visibleRows().then((shown) => {
      expect(shown.slice(0, 3)).to.deep.equal(["# active 15", "# planned 10", "s03"]);
      expect(shown).to.have.length(12);
    });
    header("planned").should("have.attr", "aria-expanded", "true");
    header("planned").click();
    visibleRows().should("deep.equal", ["# active 15", "# planned 10"]);
  });

  it("nests groups", () => {
    groupBy([
      { id: "tags", label: "Tags" },
      { id: "status", label: "Status" },
    ]);
    visibleRows().should("deep.equal", ["# blue 1", "# red 1", "# No tags 24"]);
    header("blue").click();
    header("active 1").click();
    visibleRows().should("deep.equal", [
      "# blue 1",
      "# active 1",
      "s00",
      "# red 1",
      "# No tags 24",
    ]);
  });

  it("pages through open groups with the table's paginator", () => {
    groupBy([{ id: "status", label: "Status" }]);
    header("active").click();
    header("planned").click();
    // 2 headers and 25 rows: 20, then 7, per page.
    cy.get(".p-paginator-page").should("have.length", 2);
    cy.get(".p-paginator-page").contains("2").click();
    // The page continues "planned", so its header is shown again.
    visibleRows().then((shown) => {
      expect(shown[0]).to.equal("# planned 10");
      expect(shown.filter((row) => !row.startsWith("#"))).to.have.length(7);
    });
  });

  it("sorts rows within their groups", () => {
    groupBy([{ id: "status", label: "Status" }]);
    header("active").click();
    cy.get(".p-datatable-sortable-column").contains("ID").as("idHeader");
    // Ascending, then descending.
    cy.get("@idHeader").click();
    cy.get("@idHeader").click();
    visibleRows().then((shown) => expect(shown.slice(0, 2)).to.deep.equal(["# active 15", "s22"]));
  });

  it("selects a row listed in several groups once", () => {
    groupBy([{ id: "tags", label: "Tags" }]);
    header("blue").click();
    header("red").click();
    cy.get(".p-datatable-tbody input[type='checkbox']").first().click({ force: true });
    cy.get('[data-testid="selection-summary"]').should("contain.text", "1 item selected");
    cy.get(".p-datatable-tbody input[type='checkbox']:checked").should("have.length", 2);
  });

  it("shows every row again once ungrouped", () => {
    groupBy([{ id: "status", label: "Status" }]);
    groupBy([]);
    cy.get('[data-testid="group-header"]').should("not.exist");
    cy.get(".p-datatable-tbody > tr").should("have.length", 20);
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 25");
  });
});
