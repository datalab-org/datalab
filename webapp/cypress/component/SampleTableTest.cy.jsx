import "bootstrap/dist/css/bootstrap.css";
import DynamicDataTable from "@/components/DynamicDataTable.vue";
import SampleTable from "@/components/SampleTable.vue";
import UserBubble from "@/components/UserBubble.vue";
import StyledTooltip from "@/components/StyledTooltip.vue";
import DatalabPreset from "@/primevue-theme-preset.js";
import { itemTypes, SAMPLE_TABLE_TYPES } from "@/resources.js";
import { FilterOperator } from "@primevue/core/api";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

const IsoDatetimeToDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleDateString();
};

const openColumnFilter = (columnIndex) => {
  cy.get(".p-datatable-thead th").eq(columnIndex).find(".p-datatable-column-filter-button").click();
  cy.get(".p-datatable-filter-overlay").should("be.visible");
};

const selectMultiselectOption = (columnIndex, label, expectedSelected = true) => {
  openColumnFilter(columnIndex);
  cy.get(".p-datatable-filter-overlay .p-multiselect-label-container").then(($label) => {
    $label[0].click();
  });
  cy.get(".p-datatable-filter-overlay .p-multiselect [role='combobox']").should(
    "have.attr",
    "aria-expanded",
    "true",
  );
  const optionSelector = `[role="option"][aria-label="${label}"]`;
  cy.get(".p-multiselect-list-container:visible").find(optionSelector).should("be.visible").click();
  // PrimeVue rerenders the draft value after selection; apply it before checking filtered rows.
  cy.get(".p-datatable-filter-overlay .p-multiselect").should(
    expectedSelected ? "contain.text" : "not.contain.text",
    label,
  );
  cy.get(".p-datatable-filter-overlay").findByText("Apply").click();
  cy.get(".p-datatable-filter-overlay").should("not.exist");
};

describe("SampleTable Component Tests", () => {
  let store;
  let wrapper;
  const originalAvailability = Object.fromEntries(
    SAMPLE_TABLE_TYPES.map((type) => [type, itemTypes[type].available]),
  );

  afterEach(() => {
    for (const [type, available] of Object.entries(originalAvailability)) {
      if (available === undefined) {
        delete itemTypes[type].available;
      } else {
        itemTypes[type].available = available;
      }
    }
  });

  // Exercise datalab's matchers through the real DataTable without repeatedly driving PrimeVue's
  // nested filter overlays. The Type test below retains one end-to-end multiselect interaction.
  const setColumnFilter = (field, value, operator = FilterOperator.AND) => {
    cy.then(() => {
      const dataTable = wrapper.findComponent(DynamicDataTable);
      dataTable.vm.filters[field].operator = operator;
      dataTable.vm.filters[field].constraints[0].value = value;
      return dataTable.vm.$nextTick();
    });
  };

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
              blocks: [{ blocktype: "nmr", title: "NMR" }],
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
              blocks: [
                { blocktype: "nmr", title: "NMR" },
                { blocktype: "insitu", title: "NMR (in situ)" },
              ],
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
              blocks: [
                { blocktype: "nmr", title: "NMR" },
                { blocktype: "insitu", title: "NMR (in situ)" },
                { blocktype: "ftir", title: "FTIR" },
              ],
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
              blocks: [{ blocktype: "nmr", title: "NMR" }],
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
              blocks: [
                { blocktype: "nmr", title: "NMR" },
                { blocktype: "xrd", title: "XRD" },
              ],
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
              blocks: [{ blocktype: "nmr", title: "NMR" }],
            },
          ],
        };
      },
    });

    cy.mount(SampleTable, {
      global: {
        plugins: [store, [PrimeVue, { theme: DatalabPreset }]],
        config: {
          globalProperties: {
            $filters: {
              IsoDatetimeToDate,
            },
          },
        },
        components: {
          UserBubble,
          StyledTooltip,
        },
      },
    }).then(({ wrapper: mountedWrapper }) => {
      wrapper = mountedWrapper;
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

  it("disables item creation controls when no supported item types are available", () => {
    for (const type of SAMPLE_TABLE_TYPES) {
      itemTypes[type].available = false;
    }

    cy.get('[data-testid="add-item-button"]').should("be.disabled");
    cy.get('[data-testid="add-item-button"]')
      .parent()
      .should(
        "have.attr",
        "title",
        "No item types are available for single-item creation on this deployment",
      );
    cy.get('[data-testid="batch-item-button"]').should("be.disabled");
    cy.get('[data-testid="batch-item-button"]')
      .parent()
      .should(
        "have.attr",
        "title",
        "No item types are available for batch creation on this deployment",
      );
  });

  it("closes table settings outside but keeps them open when selecting columns", () => {
    cy.get('[data-testid="table-settings-button"]').click();
    cy.get('[data-testid="table-settings-menu"]').should("be.visible");
    cy.get('[data-testid="search-input"]').click();
    cy.get('[data-testid="table-settings-menu"]').should("not.be.visible");

    cy.get('[data-testid="table-settings-button"]').click();
    cy.get('[data-testid="table-settings-menu"]').find(".p-multiselect-label-container").click();
    cy.get('[data-testid="table-settings-menu"]').find(".p-multiselect-option").first().click();
    cy.get('[data-testid="table-settings-menu"]').should("be.visible");
  });

  it("lays out the Sample action buttons responsively", () => {
    const actionButtons = [
      '[data-testid="add-item-button"]',
      '[data-testid="batch-item-button"]',
      '[data-testid="scan-qr-button"]',
    ].join(", ");

    cy.viewport(375, 720);
    cy.get(actionButtons).should(($buttons) => {
      const tops = [...$buttons].map((button) => Math.round(button.getBoundingClientRect().top));
      const widths = [...$buttons].map((button) =>
        Math.round(button.getBoundingClientRect().width),
      );

      expect(new Set(tops).size).to.equal(3);
      expect(new Set(widths).size).to.equal(1);
    });

    cy.viewport(600, 720);
    cy.get(actionButtons).should(($buttons) => {
      const tops = [...$buttons].map((button) => Math.round(button.getBoundingClientRect().top));
      expect(new Set(tops).size).to.equal(1);
    });
  });

  it("keeps the table rows in place when selecting an item", () => {
    cy.viewport(1280, 720);

    let initialRowTop;
    let actionsRight;

    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 6");
    cy.get('[data-testid="selected-dropdown"]').should("not.exist");

    cy.get(".p-datatable-tbody > tr")
      .first()
      .then(($row) => {
        initialRowTop = $row[0].getBoundingClientRect().top;
      });

    cy.get(".p-datatable-tbody > tr").first().find("input[type='checkbox']").click({ force: true });

    cy.get('[data-testid="selection-summary"]').should("contain.text", "1 item selected");
    cy.get('[data-testid="selected-dropdown"]')
      .should("contain.text", "Actions")
      .then(($button) => {
        actionsRight = $button[0].getBoundingClientRect().right;
      });
    cy.get(".p-datatable-tbody > tr")
      .first()
      .should(($row) => {
        expect($row[0].getBoundingClientRect().top).to.equal(initialRowTop);
      });

    cy.get(".p-datatable-tbody > tr").eq(1).find("input[type='checkbox']").click({ force: true });

    cy.get('[data-testid="selection-summary"]').should("contain.text", "2 items selected");
    cy.get('[data-testid="selected-dropdown"]').should(($button) => {
      expect($button[0].getBoundingClientRect().right).to.equal(actionsRight);
    });

    cy.get(".p-datatable-tbody > tr").first().find("input[type='checkbox']").click({ force: true });
    cy.get(".p-datatable-tbody > tr").eq(1).find("input[type='checkbox']").click({ force: true });

    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 6");
    cy.get('[data-testid="selected-dropdown"]').should("not.exist");
  });

  it("renders the table with correct headers", () => {
    const headers = [
      "", //checkbox
      "ID",
      "Type",
      "Status",
      "Name",
      "Formula",
      "Date",
      "Collections",
      "Creators",
      "", // nblocks
      "", // nfiles
      "", // last_modified
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
            cy.get("td").eq(columnIndices["Name"]).should("contain.text", "Sample 1");
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
            cy.get("td").eq(columnIndices["Name"]).should("contain.text", "Cell 1");
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
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 1");
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Sample 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get('[data-testid="search-input"]').type("Cell 1");
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Cell 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get('[data-testid="search-input"]').type("Cell");
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 3");
    cy.get(".p-datatable-tbody tr").eq(0).should("contain.text", "Cell 1");

    cy.get('[data-testid="search-input"]').clear();
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 6");
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
          .eq(columnIndices["Name"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Name"])
          .should("contain.text", "Cell 1");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Name"])
          .should("contain.text", "Cell 2");

        cy.get(".p-datatable-thead th")
          .eq(columnIndices["Name"])
          .find(".p-datatable-sort-icon")
          .click();
        cy.get(".p-datatable-tbody tr")
          .eq(0)
          .find("td")
          .eq(columnIndices["Name"])
          .should("contain.text", "Sample 3");
        cy.get(".p-datatable-tbody tr")
          .eq(1)
          .find("td")
          .eq(columnIndices["Name"])
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
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 3");

    cy.get(".p-datatable-thead th").eq(1).find(".p-datatable-column-filter-button").click();
    cy.get(".p-datatable-filter-overlay").find(".p-inputtext").clear();
    cy.get(".p-datatable-filter-overlay").find(".p-inputtext").type("sample1");
    cy.get(".p-datatable-filter-overlay").findByText("Apply").click();
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    cy.get('[data-testid="selection-summary"]').should("contain.text", "Number of items: 1");
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "sample1");
  });

  it("filters by Type correctly", () => {
    selectMultiselectOption(2, "samples");
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "sample1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "sample2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(1).should("contain.text", "sample3");

    selectMultiselectOption(2, "samples", false);
    selectMultiselectOption(2, "cells");
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    cy.get(".p-datatable-tbody tr").eq(0).find("td").eq(1).should("contain.text", "cell1");
    cy.get(".p-datatable-tbody tr").eq(1).find("td").eq(1).should("contain.text", "cell2");
    cy.get(".p-datatable-tbody tr").eq(2).find("td").eq(1).should("contain.text", "cell3");
  });

  it("filters by Status correctly", () => {
    const statuses = ["ACTIVE", "CYCLED", "PLANNED", "FAILED", "SHORTED", "DISMANTLED"].map(
      (status) => ({ status }),
    );

    setColumnFilter("status", [statuses[0]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);

    setColumnFilter("status", [statuses[1]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);

    setColumnFilter("status", statuses.slice(0, 1));
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    setColumnFilter("status", statuses.slice(0, 2));
    cy.get(".p-datatable-tbody tr").should("have.length", 2);
    setColumnFilter("status", statuses.slice(0, 3));
    cy.get(".p-datatable-tbody tr").should("have.length", 3);
    setColumnFilter("status", statuses.slice(0, 4));
    cy.get(".p-datatable-tbody tr").should("have.length", 4);
    setColumnFilter("status", statuses.slice(0, 5));
    cy.get(".p-datatable-tbody tr").should("have.length", 5);
    setColumnFilter("status", statuses);
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Collections correctly", () => {
    const collections = ["collection1", "collection2", "collection3"].map((collection_id) => ({
      collection_id,
    }));

    setColumnFilter("collections", [collections[0]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 4);

    setColumnFilter("collections", [collections[1]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 3);

    setColumnFilter("collections", [collections[2]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 2);

    setColumnFilter("collections", collections);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    setColumnFilter("collections", collections, FilterOperator.OR);
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Creators correctly", () => {
    const creators = ["Creator 1", "Creator 2", "Creator 3"].map((display_name) => ({
      display_name,
      type: "creator",
    }));

    setColumnFilter("creatorsAndGroups", [creators[0]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 4);

    setColumnFilter("creatorsAndGroups", [creators[1]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 4);

    setColumnFilter("creatorsAndGroups", [creators[2]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 2);

    setColumnFilter("creatorsAndGroups", creators);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    setColumnFilter("creatorsAndGroups", creators, FilterOperator.OR);
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });

  it("filters by Blocks correctly", () => {
    const blockTypes = ["nmr", "insitu", "ftir", "xrd"].map((blocktype) => ({ blocktype }));

    setColumnFilter("blocks", [blockTypes[0]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 6);

    setColumnFilter("blocks", [blockTypes[1]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 2);

    setColumnFilter("blocks", [blockTypes[2]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);

    setColumnFilter("blocks", [blockTypes[3]]);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);

    setColumnFilter("blocks", blockTypes);
    cy.get(".p-datatable-tbody tr").should("have.length", 1);
    setColumnFilter("blocks", blockTypes, FilterOperator.OR);
    cy.get(".p-datatable-tbody tr").should("have.length", 6);
  });
});

// A realistically "messy" table: many rows, each with several creators, groups, tags,
// collections and blocks. Rendering cost should scale gently with the number of rows, so these
// check per-row budgets (DOM size, global listeners) rather than timings, which are too noisy
// to assert on in CI.
describe("SampleTable with many messy rows", () => {
  const NUM_ROWS = 100;
  // Budget of DOM elements added per rendered row, including anything teleported to <body>,
  // set ~20% above the measured value. Raise it deliberately if a change legitimately needs more.
  const MAX_ELEMENTS_PER_ROW = 85;

  const FORMULAE = ["LiNi0.8Mn0.1Co0.1O2", "Na3V2(PO4)3", "CuSO4.5H2O", "LiFePO4", "Li2CO3"];
  const TAGS = Array.from({ length: 5 }, (_, i) => ({
    type: "tags",
    immutable_id: `tag${i}`,
    name: `tag-${i}`,
    color: "#3366ff",
    description: `A description of tag ${i}`,
  }));
  const CREATORS = Array.from({ length: 4 }, (_, i) => ({
    display_name: `Messy Creator ${i}`,
    immutable_id: `creator${i}`,
  }));
  const GROUPS = Array.from({ length: 3 }, (_, i) => ({
    display_name: `Messy Group ${i}`,
    group_id: `group${i}`,
    immutable_id: `group${i}`,
  }));
  const BLOCKS = ["nmr", "xrd", "cycle", "raman"].map((blocktype) => ({
    blocktype,
    title: blocktype,
  }));

  const makeMessySamples = (n) =>
    Array.from({ length: n }, (_, i) => {
      const blocks = BLOCKS.slice(0, i % 5);
      return {
        item_id: `messy_${String(i).padStart(3, "0")}`,
        type: i % 3 === 0 ? "cells" : "samples",
        name: `Messy sample number ${i} with a reasonably long name`,
        status: ["PLANNED", "ACTIVE", "FAILED", "CYCLED"][i % 4],
        chemform: FORMULAE[i % FORMULAE.length],
        date: new Date(Date.UTC(2023, 0, 1 + (i % 300))).toISOString(),
        last_modified: new Date(Date.UTC(2024, 0, 1 + (i % 300))).toISOString(),
        collections: Array.from({ length: i % 4 }, (_, j) => ({
          collection_id: `collection${j}`,
        })),
        creators: CREATORS.slice(0, 1 + (i % CREATORS.length)),
        groups: i % 5 === 0 ? GROUPS.slice(0, 1) : i % 7 === 0 ? GROUPS.slice(0, 2) : [],
        nblocks: blocks.length,
        nfiles: i % 3,
        blocks,
        tags: TAGS.slice(0, i % (TAGS.length + 1)),
      };
    });

  let listenerSpies;
  let elementsBefore;
  let bodyChildrenBefore;

  const countListeners = (spy, type) =>
    spy.getCalls().filter((call) => call.args[0] === type).length;

  beforeEach(() => {
    localStorage.removeItem("datatable-state-samples");

    const store = createStore({
      state() {
        return {
          datatablePaginationSettings: { samples: { page: 0, rows: NUM_ROWS } },
          serverInfo: { features: { tags: true } },
          tag_list: TAGS,
          blocksInfos: {},
          sample_list: Object.freeze(makeMessySamples(NUM_ROWS)),
        };
      },
      mutations: {
        setPage(state, { type, page }) {
          state.datatablePaginationSettings[type].page = page;
        },
        setRows(state, { type, rows }) {
          state.datatablePaginationSettings[type].rows = rows;
        },
      },
    });

    cy.window().then((win) => {
      elementsBefore = win.document.getElementsByTagName("*").length;
      bodyChildrenBefore = win.document.body.children.length;
      listenerSpies = {
        document: cy.spy(win.document, "addEventListener"),
        window: cy.spy(win, "addEventListener"),
      };
    });

    cy.mount(SampleTable, {
      global: {
        plugins: [store, [PrimeVue, { theme: DatalabPreset }]],
        config: { globalProperties: { $filters: { IsoDatetimeToDate } } },
        components: { UserBubble, StyledTooltip },
      },
    });
    cy.get(".p-datatable-tbody > tr").should("have.length", NUM_ROWS);
  });

  it("shows a tooltip when hovering a creator", () => {
    cy.get(".p-datatable-tbody tr")
      .first()
      .find(".avatar")
      .first()
      .closest(".tooltip-anchor")
      .trigger("mouseenter");
    cy.get("[data-testid='styled-tooltip'][data-show]")
      .should("have.length", 1)
      .and("contain.text", "Messy Creator 0");
  });

  it("keeps the DOM size per row within budget", () => {
    cy.window().then((win) => {
      const added = win.document.getElementsByTagName("*").length - elementsBefore;
      const teleported = win.document.body.children.length - bodyChildrenBefore;
      const perRow = added / NUM_ROWS;
      const teleportedPerRow = teleported / NUM_ROWS;
      const summary =
        `${NUM_ROWS} rows added ${added} elements (${perRow.toFixed(1)} per row, ` +
        `budget ${MAX_ELEMENTS_PER_ROW}); ${teleported} top-level elements teleported to ` +
        `<body> (${teleportedPerRow.toFixed(1)} per row)`;
      cy.task("log", summary);
      expect(perRow, summary).to.be.at.most(MAX_ELEMENTS_PER_ROW);
      // Tooltips/popovers should only be rendered into <body> once they are first shown,
      // so nothing should be teleported before any interaction
      expect(teleported, summary).to.equal(0);
    });
  });

  it("does not add global listeners per row on mount", () => {
    // Every row has several tooltips (creators, tags, block/file counters, groups), so any
    // per-tooltip document/window listener would scale with the number of rows
    cy.then(() => {
      expect(countListeners(listenerSpies.document, "mousedown")).to.be.lessThan(10);
      expect(countListeners(listenerSpies.window, "scroll")).to.be.lessThan(10);
    });
  });
});
