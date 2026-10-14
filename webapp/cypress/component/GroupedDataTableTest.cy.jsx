import GroupedDataTable from "@/components/GroupedDataTable.vue";

const tag = (immutable_id, name) => ({ type: "tags", immutable_id, name, color: "#f1c40f" });
const air = tag("aaaaaaaaaaaaaaaaaaaaaaaa", "air-sensitive");
const cathode = tag("bbbbbbbbbbbbbbbbbbbbbbbb", "cathode");

const items = [
  { item_id: "s1", name: "Sample 1", tags: [air, cathode] },
  { item_id: "s2", name: "Sample 2", tags: [cathode] },
  { item_id: "s3", name: "Sample 3", tags: [] },
];

const columns = [
  { field: "item_id", header: "ID" },
  { field: "tags", header: "Tags" },
];

describe("GroupedDataTable.vue", () => {
  it("groups by tag, listing an item under each of its tags", () => {
    cy.mount(GroupedDataTable, {
      props: { items, groupFields: [{ id: "tags", label: "Tags" }], itemsSelected: [], columns },
    });

    cy.get(".list-group-item-action").should("have.length", 3);
    cy.get(".list-group-item-action").eq(0).should("contain", "air-sensitive").and("contain", "1");
    cy.get(".list-group-item-action").eq(1).should("contain", "cathode").and("contain", "2");
    cy.get(".list-group-item-action").eq(2).should("contain", "No tags").and("contain", "1");

    // Expanding a group shows its items, with their tag names in the Tags column.
    cy.get(".list-group-item-action").eq(1).click();
    cy.get("tbody tr").should("have.length", 2);
    cy.get("tbody tr").eq(0).should("contain", "s1").and("contain", "air-sensitive, cathode");
  });

  it("orders date groups newest first, with undated items last", () => {
    const dated = [
      { item_id: "jan", date: "2026-01-15T12:00:00" },
      { item_id: "apr", date: "2026-04-15T12:00:00" },
      { item_id: "feb", date: "2026-02-15T12:00:00" },
      { item_id: "none" },
    ];
    cy.mount(GroupedDataTable, {
      props: {
        items: dated,
        groupFields: [{ id: "date", label: "Date", grain: "month" }],
        itemsSelected: [],
        columns,
      },
    });
    const month = (m) =>
      new Date(2026, m, 15).toLocaleDateString(undefined, { month: "long", year: "numeric" });
    cy.get(".list-group-item-action").then((buttons) => {
      const labels = [...buttons].map((b) => b.innerText);
      expect(labels[0]).to.contain(month(3));
      expect(labels[1]).to.contain(month(1));
      expect(labels[2]).to.contain(month(0));
      expect(labels[3]).to.contain("No date");
    });
  });

  it("groups by the stored date, like the Date column, whatever the time", () => {
    const sameDay = [
      { item_id: "early", date: "2026-05-03T00:30:00" },
      { item_id: "late", date: "2026-05-03T23:30:00+00:00" },
    ];
    cy.mount(GroupedDataTable, {
      props: {
        items: sameDay,
        groupFields: [{ id: "date", label: "Date", grain: "day" }],
        itemsSelected: [],
        columns,
      },
    });
    const label = new Date(Date.UTC(2026, 4, 3)).toLocaleDateString(undefined, {
      timeZone: "UTC",
    });
    cy.get(".list-group-item-action").should("have.length", 1).and("contain", label);
  });
});
