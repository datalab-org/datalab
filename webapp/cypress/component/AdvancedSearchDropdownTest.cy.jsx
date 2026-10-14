import AdvancedSearchDropdown from "@/components/AdvancedSearchDropdown.vue";

const mountWithColumns = (fields) =>
  cy.mount(AdvancedSearchDropdown, {
    props: {
      activeFilters: [],
      groupByFields: [],
      availableColumns: fields.map((field) => ({ field, header: field })),
      advancedQueryConfig: null,
    },
  });

const option = (label) => cy.contains("button.dropdown-item", new RegExp(`^\\s*${label}\\s*$`));

describe("AdvancedSearchDropdown.vue", () => {
  it("offers every option on a table with all the columns they read", () => {
    mountWithColumns(["item_id", "type", "status", "date", "creatorsAndGroups", "blocks", "tags"]);
    ["My items", "Latest items \\(past week\\)", "Active", "Have blocks"].forEach((label) =>
      option(label).should("not.be.disabled"),
    );
    ["Type", "Creators", "Status", "Date", "Tags"].forEach((label) =>
      option(label).should("not.be.disabled"),
    );
  });

  it("disables options whose column the table does not show", () => {
    // e.g. the collections table: creators, but no date, status, blocks, type or tags
    mountWithColumns(["collection_id", "title", "creatorsAndGroups"]);
    option("My items").should("not.be.disabled");
    option("Creators").should("not.be.disabled");
    ["Latest items \\(past week\\)", "Active", "Have blocks"].forEach((label) =>
      option(label).should("be.disabled").and("have.attr", "title", "Not applicable to this table"),
    );
    ["Type", "Status", "Date", "Tags"].forEach((label) => option(label).should("be.disabled"));
  });
});
