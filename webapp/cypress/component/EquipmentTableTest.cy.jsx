import EquipmentTable from "@/components/EquipmentTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

const IsoDatetimeToDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleDateString();
};

describe("EquipmentTable Component Tests", () => {
  let store;

  beforeEach(() => {
    store = createStore({
      state() {
        return {
          datatablePaginationSettings: {
            equipment: {
              page: 0,
              rows: 20,
            },
          },
          equipment_list: [
            {
              item_id: "equipment1",
              type: "equipment",
              name: "Equipment One",
              date: "2023-09-01T12:34:56Z",
              location: "Warehouse A",
              creators: [{ display_name: "Maintainer A" }],
            },
            {
              item_id: "equipment2",
              type: "equipment",
              name: "Equipment Two",
              date: "2023-08-15T08:45:30Z",
              location: "Warehouse B",
              creators: [{ display_name: "Maintainer B" }, { display_name: "Maintainer C" }],
            },
          ],
        };
      },
    });

    cy.mount(EquipmentTable, {
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
    cy.get('[data-testid="add-item-button"]').should("not.exist");
    cy.get('[data-testid="batch-item-button"]').should("not.exist");
    cy.get('[data-testid="scan-qr-button"]').should("not.exist");
    cy.get('[data-testid="add-collection-button"]').should("not.exist");
    cy.get('[data-testid="add-starting-material-button"]').should("not.exist");
    cy.get('[data-testid="add-equipment-button"]').should("exist");
    cy.get('[data-testid="add-to-collection-button"]').should("not.exist");
    cy.get('[data-testid="delete-selected-button"]').should("not.exist");
    cy.get('[data-testid="search-input"]').should("exist");
  });

  it("renders the correct columns in the table", () => {
    const headers = [
      "", // checkbox
      "ID",
      "Status",
      "Name",
      "Date",
      "Location",
      "Maintainers",
    ];

    cy.get(".p-datatable-column-header-content").should("have.length", headers.length);
    cy.get(".p-datatable-column-header-content").each((header, index) => {
      cy.wrap(header).should("contain.text", headers[index]);
    });
  });

  it("displays data from the Vuex store", () => {
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "equipment1");
        cy.get("td").eq(3).should("contain.text", "Equipment One");
        cy.get("td").eq(4).should("contain.text", "9/1/2023");
        cy.get("td").eq(5).should("contain.text", "Warehouse A");
        cy.get("td").eq(6).find(".avatar").should("have.length", 1);
      });

    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "equipment2");
        cy.get("td").eq(3).should("contain.text", "Equipment Two");
        cy.get("td").eq(4).should("contain.text", "8/15/2023");
        cy.get("td").eq(5).should("contain.text", "Warehouse B");
        cy.get("td").eq(6).find(".avatar").should("have.length", 2);
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

  it("renders the component Creators", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(6).find(".avatar").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(6).find(".avatar").should("exist");
      });
  });
});
