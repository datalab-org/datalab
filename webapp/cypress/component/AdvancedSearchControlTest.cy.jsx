import AdvancedSearchControl from "@/components/AdvancedSearchControl.vue";
import PrimeVue from "primevue/config";

const TYPES = [
  { id: "samples", label: "Sample" },
  { id: "cells", label: "Cell" },
];
const COLUMNS = ["item_id", "status", "date", "creatorsAndGroups", "blocks"].map((field) => ({
  field,
  header: field,
}));

function mountControl() {
  const onResultKeys = cy.spy().as("resultKeys");
  cy.mount(AdvancedSearchControl, {
    props: {
      dataType: "samples",
      search: null,
      groupByFields: [],
      availableColumns: COLUMNS,
      "onUpdate:resultKeys": onResultKeys,
    },
    global: { plugins: [PrimeVue] },
  });
}

// The menu stays open while filters are picked.
const pick = (label) => {
  cy.get('[data-testid="advanced-search-chevron"]').then((chevron) => {
    if (chevron.attr("aria-expanded") !== "true") cy.wrap(chevron).click();
  });
  cy.contains("button.dropdown-item", new RegExp(`^\\s*${label}\\s*$`)).click();
};

describe("AdvancedSearchControl.vue", () => {
  beforeEach(() => {
    cy.intercept("GET", "**/query/types*", { body: { status: "success", types: TYPES } });
    cy.intercept("GET", "**/query/*/schema", { body: { status: "success", fields: [] } });
  });

  it("runs quick filters as OPTIMADE filters on every type of the table", () => {
    cy.intercept("GET", "**/query/samples?*", {
      body: { status: "success", items: [{ item_id: "s1" }], total: 1, next_offset: null },
    }).as("samples");
    cy.intercept("GET", "**/query/cells?*", {
      body: { status: "success", items: [{ item_id: "c1" }], total: 1, next_offset: null },
    }).as("cells");
    mountControl();

    pick("Active");
    cy.wait("@samples")
      .its("request.url")
      .then((url) => {
        expect(new URL(url).searchParams.get("filter")).to.equal(
          '(status = "active" OR status = "working" OR status = "available")',
        );
      });
    cy.wait("@cells");
    cy.get("@resultKeys")
      .its("lastCall.args.0")
      .then((keys) => expect([...keys]).to.have.members(["s1", "c1"]));

    pick("My items");
    cy.wait("@samples").its("request.url").should("include", "mine=true");
  });

  it("stops filtering once the quick filters are removed", () => {
    cy.intercept("GET", "**/query/samples?*", {
      body: { status: "success", items: [], total: 0, next_offset: null },
    });
    cy.intercept("GET", "**/query/cells?*", {
      body: { status: "success", items: [], total: 0, next_offset: null },
    });
    mountControl();

    pick("Have blocks");
    cy.contains(".badge", "Have blocks").find("button").click();
    cy.get("@resultKeys").should((spy) => expect(spy.lastCall.args[0]).to.equal(null));
  });

  it("shows why a search failed", () => {
    cy.intercept("GET", "**/query/samples?*", {
      statusCode: 400,
      body: { status: "error", message: "Cannot sort on 'x'" },
    });
    cy.intercept("GET", "**/query/cells?*", {
      body: { status: "success", items: [], total: 0, next_offset: null },
    });
    mountControl();

    pick("Active");
    cy.get('[data-testid="advanced-search-error"]').should("contain.text", "Cannot sort on 'x'");
  });
});
