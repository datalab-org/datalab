import SampleTable from "@/components/SampleTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

const IsoDatetimeToDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleDateString();
};

describe("SampleTable Component Tests", () => {
  let store;

  beforeEach(() => {
    store = createStore({
      state() {
        return {
          datatablePaginationSettings: {
            samples: {
              page: 0,
              rows: 20,
            },
          },
          sample_list: [
            {
              item_id: "sample1",
              type: "samples",
              name: "Sample 1",
              chemform: "H2O",
              date: "2023-09-01T12:34:56Z",
              collections: ["collection1"],
              creators: [{ display_name: "Creator 1" }],
              nblocks: 1,
            },
            {
              item_id: "cell2",
              type: "cells",
              name: "Cell 2",
              chemform: "CH4",
              date: "2023-08-15T08:45:30Z",
              collections: ["collection1", "collection2"],
              creators: [{ display_name: "Creator 1" }, { display_name: "Creator 2" }],
              nblocks: 2,
            },
          ],
        };
      },
    });

    cy.mount(SampleTable, {
      global: {
        plugins: [store, PrimeVue],
        config: {
          globalProperties: {
            $filters: {
              IsoDatetimeToDate,
            },
          },
        },
      },
    });
  });

  it("renders the correct buttons", () => {
    cy.get('[data-testid="add-item-button"]').should("exist");
    cy.get('[data-testid="batch-item-button"]').should("exist");
    cy.get('[data-testid="scan-qr-button"]').should("exist");
    cy.get('[data-testid="add-collection-button"]').should("not.exist");
    cy.get('[data-testid="add-starting-material-button"]').should("not.exist");
    cy.get('[data-testid="add-equipment-button"]').should("not.exist");
    cy.get('[data-testid="add-to-collection-button"]').should("not.exist");
    cy.get('[data-testid="delete-selected-button"]').should("not.exist");
    cy.get('[data-testid="search-input"]').should("exist");
  });

  it("renders the table with correct headers", () => {
    const headers = [
      "", //checkbox
      "ID",
      "Type",
      "Sample name",
      "Formula",
      "Date",
      "Collections",
      "Creators",
      "# of blocks",
    ];

    cy.get(".p-datatable-column-header-content").should("have.length", headers.length);
    cy.get(".p-datatable-column-header-content").each((header, index) => {
      cy.wrap(header).should("contain.text", headers[index]);
    });
  });

  it("displays data from the Vuex store", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "sample1");
        cy.get("td").eq(2).should("contain.text", "samples");
        cy.get("td").eq(3).should("contain.text", "Sample 1");
        cy.get("td").eq(4).should("contain.text", "H2O");
        cy.get("td").eq(5).should("contain.text", "9/1/2023");
        cy.get("td").eq(6).find(".badge").should("have.length", 1);
        cy.get("td").eq(7).find(".avatar").should("have.length", 1);
        cy.get("td").eq(8).should("contain.text", "1");
      });

    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "cell2");
        cy.get("td").eq(2).should("contain.text", "cells");
        cy.get("td").eq(3).should("contain.text", "Cell 2");
        cy.get("td").eq(4).should("contain.text", "CH4");
        cy.get("td").eq(5).should("contain.text", "8/15/2023");
        cy.get("td").eq(6).find(".badge").should("have.length", 2);
        cy.get("td").eq(7).find(".avatar").should("have.length", 2);
        cy.get("td").eq(8).should("contain.text", "2");
      });
  });

  it("renders the component FormattedItemName", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(1).find(".formatted-item-name").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(1).find(".formatted-item-name").should("exist");
      });
  });

  it("renders the component FormattedCollectionName", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(6).find(".formatted-collection-name").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(6).find(".formatted-collection-name").should("exist");
      });
  });

  it("renders the component Creators", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(7).find(".avatar").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(7).find(".avatar").should("exist");
      });
  });
});
