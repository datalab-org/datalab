import DynamicDataTable from "@/components/DynamicDataTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";
import { ITEM_ID_COLUMN, STATUS_COLUMN } from "@/utils/tableColumns.js";
import { countGroups, createRowGrouping, groupValue } from "@/utils/tableGrouping.js";

const tag = (name) => ({ type: "tags", immutable_id: name, name });

describe("tableGrouping", () => {
  it("groups an item by its whole set of tags", () => {
    const field = { id: "tags", label: "Tags" };
    expect(groupValue({ tags: [tag("cathode"), tag("air")] }, field)).to.deep.equal(
      groupValue({ tags: [tag("air"), tag("cathode")] }, field),
    );
    expect(groupValue({ tags: [tag("cathode"), tag("air")] }, field).label).to.equal(
      "air, cathode",
    );
  });

  it("groups dates by the stored calendar month", () => {
    const value = groupValue({ date: "2026-01-31T23:30:00" }, { id: "date", grain: "month" });
    expect(value.key).to.equal("2026-01");
  });

  it("sorts rows without a value last and labels them", () => {
    const { groupKey, labelOf } = createRowGrouping([{ id: "status", label: "Status" }]);
    const keys = [{ status: "planned" }, {}, { status: "active" }].map(groupKey).sort();
    expect(keys.map(labelOf)).to.deep.equal(["active", "planned", "No status"]);
  });

  it("combines several fields into one group", () => {
    const { groupKey, labelOf } = createRowGrouping([
      { id: "type", label: "Type" },
      { id: "status", label: "Status" },
    ]);
    expect(labelOf(groupKey({ type: "samples", status: "active" }))).to.equal("samples › active");
  });

  it("counts the rows of each group", () => {
    const { groupKey } = createRowGrouping([{ id: "status", label: "Status" }]);
    const counts = countGroups([{ status: "a" }, { status: "a" }, { status: "b" }], groupKey);
    expect(counts.get(groupKey({ status: "a" }))).to.equal(2);
  });
});

describe("DynamicDataTable grouping", () => {
  let table;
  // 25 rows over two pages of 20: 15 active, then 10 planned.
  const rows = Array.from({ length: 25 }, (_, i) => ({
    item_id: `s${String(i).padStart(2, "0")}`,
    type: "samples",
    status: i % 5 < 3 ? "active" : "planned",
  }));

  const groupHeaders = () =>
    cy
      .get('[data-testid="group-header"]')
      .then((headers) =>
        [...headers].map((header) => header.textContent.replace(/\s+/g, " ").trim()),
      );

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

  it("shows group headers inside the table, with the counts of whole groups", () => {
    groupBy([{ id: "status", label: "Status" }]);
    groupHeaders().should("deep.equal", ["active 15", "planned 10"]);
    cy.get(".p-datatable-thead th").should("contain.text", "Status");
  });

  it("pages through the grouped rows with the table's paginator", () => {
    groupBy([{ id: "status", label: "Status" }]);
    cy.get(".p-paginator-page").should("have.length", 2);
    cy.get(".p-paginator-page").contains("2").click();
    // The group continuing from the previous page repeats its header.
    groupHeaders().should("deep.equal", ["planned 10"]);
    cy.get(".p-datatable-tbody > tr").should("have.length", 6);
  });

  it("keeps groups together when sorting by another column", () => {
    groupBy([{ id: "status", label: "Status" }]);
    cy.get(".p-datatable-sortable-column").contains("ID").as("idHeader");
    // Ascending, then descending.
    cy.get("@idHeader").click();
    cy.get("@idHeader").click();
    groupHeaders().should("deep.equal", ["active 15", "planned 10"]);
    cy.get(".p-datatable-tbody > tr").eq(1).should("contain.text", "s22");
  });

  it("shows every row again once ungrouped", () => {
    groupBy([{ id: "status", label: "Status" }]);
    groupBy([]);
    cy.get('[data-testid="group-header"]').should("not.exist");
    cy.get(".p-datatable-tbody > tr")
      .should("have.length", 20)
      .first()
      .should("contain.text", "s00");
  });

  it("keeps the selection when grouping", () => {
    cy.get(".p-datatable-tbody > tr").first().find("input[type='checkbox']").click({ force: true });
    groupBy([{ id: "status", label: "Status" }]);
    cy.get('[data-testid="selection-summary"]').should("contain.text", "1 item selected");
  });
});
