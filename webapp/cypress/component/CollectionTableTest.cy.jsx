import CollectionTable from "@/components/CollectionTable.vue";
import UserBubble from "@/components/UserBubble.vue";
import StyledTooltip from "@/components/StyledTooltip.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

describe("CollectionTable Component Tests", () => {
  let store;

  beforeEach(() => {
    store = createStore({
      state() {
        return {
          datatablePaginationSettings: {
            collections: {
              page: 0,
              rows: 20,
            },
          },
          collection_list: [
            {
              collection_id: "collection1",
              type: "collections",
              title: "Collection One",
              creators: [{ display_name: "Creator A" }],
            },
            {
              collection_id: "collection2",
              type: "collections",
              title: "Collection Two",
              creators: [{ display_name: "Creator B" }, { display_name: "Creator C" }],
            },
          ],
        };
      },
    });

    cy.mount(CollectionTable, {
      global: {
        plugins: [store, PrimeVue],
        components: {
          UserBubble,
          StyledTooltip,
        },
      },
    });
  });

  it("renders the correct buttons", () => {
    cy.get('[data-testid="add-item-button"]').should("not.exist");
    cy.get('[data-testid="batch-item-button"]').should("not.exist");
    cy.get('[data-testid="scan-qr-button"]').should("not.exist");
    cy.get('[data-testid="add-collection-button"]').should("exist");
    cy.get('[data-testid="add-starting-material-button"]').should("not.exist");
    cy.get('[data-testid="add-equipment-button"]').should("not.exist");
    cy.get('[data-testid="add-to-collection-button"]').should("not.exist");
    cy.get('[data-testid="delete-selected-button"]').should("not.exist");
    cy.get('[data-testid="search-input"]').should("exist");
  });

  it("renders the correct columns in the table", () => {
    const headers = [
      "", //checkbox
      "ID",
      "Title",
      "Creators",
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
        cy.get("td").eq(1).should("contain.text", "collection1");
        cy.get("td").eq(2).should("contain.text", "Collection One");
        cy.get("td").eq(3).find(".avatar").should("have.length", 1);
      });

    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(0).should("contain.text", "");
        cy.get("td").eq(1).should("contain.text", "collection2");
        cy.get("td").eq(2).should("contain.text", "Collection Two");
        cy.get("td").eq(3).find(".avatar").should("have.length", 2);
      });
  });

  it("renders the component FormattedCollectionName", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(1).find(".formatted-collection-name").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(1).find(".formatted-collection-name").should("exist");
      });
  });

  it("renders the component Creators", () => {
    cy.get(".p-datatable-tbody tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(3).find(".avatar").should("exist");
      });
    cy.get(".p-datatable-tbody tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(3).find(".avatar").should("exist");
      });
  });
});
