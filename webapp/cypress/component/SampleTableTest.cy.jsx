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
      .eq(3)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "cell1");
        cy.get("td").eq(2).should("contain.text", "cells");
        cy.get("td").eq(3).should("contain.text", "Cell 1");
        cy.get("td").eq(4).should("contain.text", "CH4");
        cy.get("td").eq(5).should("contain.text", "8/15/2023");
        cy.get("td").eq(6).find(".badge").should("have.length", 1);
        cy.get("td").eq(7).find(".avatar").should("have.length", 2);
        cy.get("td").eq(8).should("contain.text", "1");
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
    cy.get(".p-datatable-thead th").eq(1).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "cell1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "cell2");

    cy.get(".p-datatable-thead th").eq(1).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "sample3");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "sample2");

    cy.get(".p-datatable-thead th").eq(2).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(2).should("contain.text", "cells");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(2).should("contain.text", "cells");

    cy.get(".p-datatable-thead th").eq(2).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(2).should("contain.text", "samples");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(2).should("contain.text", "samples");

    cy.get(".p-datatable-thead th").eq(3).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(3).should("contain.text", "Cell 1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(3).should("contain.text", "Cell 2");

    cy.get(".p-datatable-thead th").eq(3).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(3).should("contain.text", "Sample 3");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(3).should("contain.text", "Sample 2");

    cy.get(".p-datatable-thead th").eq(4).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(4).should("contain.text", "CH4");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(4).should("contain.text", "CH4");

    cy.get(".p-datatable-thead th").eq(4).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(4).should("contain.text", "H2O");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(4).should("contain.text", "H2O");

    cy.get(".p-datatable-thead th").eq(5).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(5).should("contain.text", "8/15/2023");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(5).should("contain.text", "8/16/2023");

    cy.get(".p-datatable-thead th").eq(5).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(5).should("contain.text", "9/3/2023");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(5).should("contain.text", "9/2/2023");

    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(6).find(".badge").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(6).find(".badge").should("have.length", 1);

    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(6).find(".badge").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(6).find(".badge").should("have.length", 2);

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(7).find(".avatar").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(7).find(".avatar").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(7).find(".avatar").should("have.length", 1);

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(7).find(".avatar").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(7).find(".avatar").should("have.length", 2);
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(7).find(".avatar").should("have.length", 2);

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(8).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(8).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(8).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(3).find("td").eq(8).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(4).find("td").eq(8).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(5).find("td").eq(8).should("contain.text", "3");

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(8).should("contain.text", "3");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(8).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(8).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(3).find("td").eq(8).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(4).find("td").eq(8).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(5).find("td").eq(8).should("contain.text", "1");

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(9).should("contain.text", "");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(9).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(9).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(3).find("td").eq(9).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(4).find("td").eq(9).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(5).find("td").eq(9).should("contain.text", "3");

    cy.get(".p-datatable-thead th").eq(9).find(".p-datatable-sort-icon").click();
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(9).should("contain.text", "3");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(9).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(9).should("contain.text", "2");
    cy.get(".p-datatable-tbody tr").eq(3).find("td").eq(9).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(4).find("td").eq(9).should("contain.text", "1");
    cy.get(".p-datatable-tbody tr").eq(5).find("td").eq(9).should("contain.text", "");
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

  it("filters by Collections correctly", () => {
    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection1").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection2").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("collection3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(6).find(".p-datatable-column-filter-button").click();
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
    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 1").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 2").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("Creator 3").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(7).find(".p-datatable-column-filter-button").click();
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
    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("NMR").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("insitu").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("FTIR").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-multiselect-label-container").click();
    cy.get(".p-multiselect-list-container").findByText("XRD").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.findByText("Clear").click();

    cy.get(".p-datatable-thead th").eq(8).find(".p-datatable-column-filter-button").click();
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
