import StartingMaterialTable from "@/components/StartingMaterialTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

const IsoDatetimeToDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleDateString();
};

describe("StartingMaterialTable Component Tests", () => {
  let store;

  beforeEach(() => {
    store = createStore({
      state() {
        return {
          datatablePaginationSettings: {
            startingMaterials: {
              page: 0,
              rows: 20,
            },
          },
          starting_material_list: [
            {
              item_id: "material1",
              type: "starting_materials",
              name: "Material One",
              chemform: "H2O",
              date: "2023-09-01",
              chemical_purity: "99%",
              location: "King's Lynn",
              barcode: "123",
              nblocks: 1,
            },
            {
              item_id: "material2",
              type: "starting_materials",
              name: "Material Two",
              chemform: "CH4",
              date: "2023-08-15",
              barcode: "456",
              location: "Hunstanton",
              chemical_purity: "95%",
              nblocks: 2,
            },
          ],
        };
      },
    });

    cy.mount(StartingMaterialTable, {
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
    cy.get('[data-testid="add-equipment-button"]').should("not.exist");
    cy.get('[data-testid="add-to-collection-button"]').should("not.exist");
    cy.get('[data-testid="delete-selected-button"]').should("not.exist");
    cy.get('[data-testid="search-input"]').should("exist");
  });

  it("renders the correct columns in the table", () => {
    const headers = [
      "", // checkbox
      "ID",
      "", // barcode
      "Name",
      "Formula",
      "Date",
      "Location",
      "", // nblocks
      "", //nfiles
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
        cy.get("td").eq(1).should("contain.text", "material1");
        cy.get("td").eq(2).should("contain.text", "123");
        cy.get("td").eq(3).should("contain.text", "Material One");
        cy.get("td").eq(4).should("contain.text", "H2O");
        cy.get("td").eq(5).should("contain.text", "9/1/2023");
        cy.get("td").eq(6).should("contain.text", "King's Lynn");
        cy.get("td").eq(7).should("contain.text", "1");
      });

    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "material2");
        cy.get("td").eq(2).should("contain.text", "456");
        cy.get("td").eq(3).should("contain.text", "Material Two");
        cy.get("td").eq(4).should("contain.text", "CH4");
        cy.get("td").eq(5).should("contain.text", "8/15/2023");
        cy.get("td").eq(6).should("contain.text", "Hunstanton");
        cy.get("td").eq(7).should("contain.text", "2");
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

  it("renders the component FormattedBarcode", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(2).find("[data-testid='formatted-barcode']").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(2).find("[data-testid='formatted-barcode']").should("exist");
      });
  });
});
