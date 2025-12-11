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
              status: "PLANNED",
              chemform: "H2O",
              date: "2023-09-01T12:34:56Z",
              collections: [{ collection_id: "collection1" }],
              creators: [{ display_name: "Creator 1" }],
              nblocks: 1,
              nfiles: 1,
              blocks: [{ title: "NMR" }],
            },
            {
              item_id: "sample2",
              type: "samples",
              name: "Sample 2",
              status: "ACTIVE",
              chemform: "H2O",
              date: "2023-09-02T12:34:56Z",
              collections: [{ collection_id: "collection2" }],
              creators: [{ display_name: "Creator 2" }],
              nblocks: 2,
              nfiles: 2,
              blocks: [{ title: "NMR" }, { title: "insitu" }],
            },
            {
              item_id: "sample3",
              type: "samples",
              name: "Sample 3",
              status: "FAILED",
              chemform: "H2O",
              date: "2023-09-03T12:34:56Z",
              collections: [{ collection_id: "collection3" }],
              creators: [{ display_name: "Creator 3" }],
              nblocks: 3,
              nfiles: 3,
              blocks: [{ title: "NMR" }, { title: "insitu" }, { title: "FTIR" }],
            },
            {
              item_id: "cell1",
              type: "cells",
              name: "Cell 1",
              status: "CYCLED",
              chemform: "CH4",
              date: "2023-08-15T08:45:30Z",
              collections: [{ collection_id: "collection1" }],
              creators: [{ display_name: "Creator 1" }, { display_name: "Creator 2" }],
              nblocks: 1,
              nfiles: 0,
              blocks: [{ title: "NMR" }],
            },
            {
              item_id: "cell2",
              type: "cells",
              name: "Cell 2",
              status: "DISMANTLED",
              chemform: "CH4",
              date: "2023-08-16T08:45:30Z",
              collections: [{ collection_id: "collection1" }, { collection_id: "collection2" }],
              creators: [{ display_name: "Creator 1" }, { display_name: "Creator 2" }],
              nblocks: 2,
              nfiles: 1,
              blocks: [{ title: "NMR" }, { title: "XRD" }],
            },
            {
              item_id: "cell3",
              type: "cells",
              name: "Cell 3",
              status: "SHORTED",
              chemform: "CH4",
              date: "2023-08-17T08:45:30Z",
              collections: [
                { collection_id: "collection1" },
                { collection_id: "collection2" },
                { collection_id: "collection3" },
              ],
              creators: [
                { display_name: "Creator 1" },
                { display_name: "Creator 2" },
                { display_name: "Creator 3" },
              ],
              nblocks: 1,
              nfiles: 2,
              blocks: [{ title: "NMR" }],
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
      "Status",
      "Sample name",
      "Formula",
      "Date",
      "Collections",
      "Creators",
      "", // nblocks
      "", // nfiles
    ];

    cy.get(".p-datatable-column-header-content").should("have.length", headers.length);
    cy.get(".p-datatable-column-header-content").each((header, index) => {
      cy.wrap(header).should("contain.text", headers[index]);
    });
  });

  it("displays data from the Vuex store", () => {
    cy.getColumnIndices({ checkbox: 0, Status: 3, nblocks: 10, nfiles: 11 }).then(
      (columnIndices) => {
        // First row - sample1
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .within(() => {
            cy.get("td").eq(columnIndices["ID"]).should("contain.text", "sample1");
            cy.get("td").eq(columnIndices["Type"]).should("contain.text", "samples");
            cy.get("td").eq(columnIndices["Sample name"]).should("contain.text", "Sample 1");
            cy.get("td").eq(columnIndices["Date"]).should("contain.text", "2023");
            cy.get("td").eq(columnIndices["Collections"]).find(".badge").should("have.length", 1);
            cy.get("td").eq(columnIndices["Creators"]).find(".avatar").should("have.length", 1);
          });

        // Fourth row - cell1
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .within(() => {
            cy.get("td").eq(columnIndices["ID"]).should("contain.text", "cell1");
            cy.get("td").eq(columnIndices["Type"]).should("contain.text", "cells");
            cy.get("td").eq(columnIndices["Sample name"]).should("contain.text", "Cell 1");
            cy.get("td").eq(columnIndices["Date"]).should("contain.text", "2023");
            cy.get("td").eq(columnIndices["Collections"]).find(".badge").should("have.length", 1);
            cy.get("td").eq(columnIndices["Creators"]).find(".avatar").should("have.length", 2);
          });
      },
    );
  });

  it("renders the component FormattedItemName", () => {
    cy.getColumnIndices({ checkbox: 0, nblocks: 10, nfiles: 11 }).then((columnIndices) => {
      cy.get(".p-datatable-tbody tr")
        .eq(0)
        .within(() => {
          cy.get("td").eq(columnIndices["ID"]).find(".formatted-item-name").should("exist");
        });
      cy.get(".p-datatable-tbody tr")
        .eq(1)
        .within(() => {
          cy.get("td").eq(columnIndices["ID"]).find(".formatted-item-name").should("exist");
        });
    });
  });

  it("renders the component FormattedCollectionName", () => {
    cy.getColumnIndices({ checkbox: 0, nblocks: 10, nfiles: 11 }).then((columnIndices) => {
      cy.get(".p-datatable-tbody tr")
        .eq(0)
        .within(() => {
          cy.get("td")
            .eq(columnIndices["Collections"])
            .find(".formatted-collection-name")
            .should("exist");
        });
      cy.get(".p-datatable-tbody tr")
        .eq(1)
        .within(() => {
          cy.get("td")
            .eq(columnIndices["Collections"])
            .find(".formatted-collection-name")
            .should("exist");
        });
    });
  });

  it("renders the component Creators", () => {
    cy.getColumnIndices({ checkbox: 0, nblocks: 10, nfiles: 11 }).then((columnIndices) => {
      cy.get(".p-datatable-tbody tr")
        .eq(0)
        .within(() => {
          cy.get("td").eq(columnIndices["Creators"]).find(".avatar").should("exist");
        });
      cy.get(".p-datatable-tbody tr")
        .eq(1)
        .within(() => {
          cy.get("td").eq(columnIndices["Creators"]).find(".avatar").should("exist");
        });
    });
  });

  it("performs global search correctly", () => {
    cy.get('[data-testid="search-input"]').type("Sample 1");
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Sample 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get('[data-testid="search-input"]').type("Cell 1");
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Cell 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get('[data-testid="search-input"]').type("Cell");
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Cell 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("sorts columns correctly", () => {
    cy.getColumnIndices({ checkbox: 0, Status: 3, nblocks: 9, nfiles: 10 }).then(
      (columnIndices) => {
        cy.get(".p-datatable-thead th")
          .eq(columnIndices["ID"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["ID"])
          .should("contain.text", "cell1");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["ID"])
          .should("contain.text", "cell2");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["ID"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["ID"])
          .should("contain.text", "sample3");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["ID"])
          .should("contain.text", "sample2");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Type"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Type"])
          .should("contain.text", "cells");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Type"])
          .should("contain.text", "cells");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Type"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Type"])
          .should("contain.text", "samples");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Type"])
          .should("contain.text", "samples");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Status"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "ACTIVE");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "CYCLED");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "DISMANTLED");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "FAILED");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "PLANNED");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "SHORTED");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Status"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "SHORTED");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "PLANNED");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "FAILED");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "DISMANTLED");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "CYCLED");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["Status"])
          .find("span")
          .should("have.attr", "title", "ACTIVE");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Sample name"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Sample name"])
          .should("contain.text", "Cell 1");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Sample name"])
          .should("contain.text", "Cell 2");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Sample name"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Sample name"])
          .should("contain.text", "Sample 3");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Sample name"])
          .should("contain.text", "Sample 2");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Date"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Date"])
          .should("contain.text", "2023");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Date"])
          .should("contain.text", "2023");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Date"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Date"])
          .should("contain.text", "2023");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Date"])
          .should("contain.text", "2023");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Collections"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Collections"])
          .find(".badge")
          .should("have.length", 1);
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Collections"])
          .find(".badge")
          .should("have.length", 1);

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Collections"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Collections"])
          .find(".badge")
          .should("have.length", 3);
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Collections"])
          .find(".badge")
          .should("have.length", 2);

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Creators"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 1);
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 1);
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 1);

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Creators"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 3);
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 2);
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["Creators"])
          .find(".avatar")
          .should("have.length", 2);

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["nblocks"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "3");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["nblocks"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "3");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["nblocks"])
          .should("contain.text", "1");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["nfiles"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "3");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["nfiles"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "3");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(2)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "2");
        cy.get(".p-datatable-tbody tr")
          .eq(3)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(4)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "1");
        cy.get(".p-datatable-tbody tr")
          .eq(5)
          .find("td")
          .eq(columnIndices["nfiles"])
          .should("contain.text", "");
      },
    );
  });

  it("filters by ID correctly", () => {
    cy.get(".p-datatable-thead th").eq(1).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-inputtext").type("sample");
    cy.get(".p-datatable-filter-overlay").findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);

    cy.get(".p-datatable-thead th").eq(1).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-inputtext").clear();
    cy.get(".p-datatable-filter-overlay").find(".p-inputtext").type("sample1");
    cy.get(".p-datatable-filter-overlay").findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "sample1");
  });

  it("filters by Type correctly", () => {
    cy.get(".p-datatable-thead th").eq(2).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("samples").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "sample1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "sample2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(1).should("contain.text", "sample3");

    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("samples").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("cells").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "cell1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "cell2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(1).should("contain.text", "cell3");
  });

  it("filters by Status correctly", () => {
    cy.get(".p-datatable-thead th").eq(3).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("ACTIVE").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(3).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("CYCLED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(3).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("ACTIVE").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("CYCLED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("PLANNED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("FAILED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("SHORTED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 5);
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("DISMANTLED").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Collections correctly", () => {
    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection1").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection2").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection1").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection2").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-filter-operator").click();
    cy.get(".p-select-list-container").findByText("Match Any").click();
    cy.findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Creators correctly", () => {
    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 1").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 2").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 1").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 2").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-filter-operator").click();
    cy.get(".p-select-list-container").findByText("Match Any").click();
    cy.findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Blocks correctly", () => {
    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("NMR").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("insitu").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("FTIR").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("XRD").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("NMR").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("insitu").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("FTIR").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("XRD").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-filter-operator").click();
    cy.get(".p-select-list-container").findByText("Match Any").click();
    cy.findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });
});
