import TagManagementTable from "@/components/TagManagementTable.vue";
import StyledTooltip from "@/components/StyledTooltip.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

const TAGS = [
  {
    immutable_id: "t1",
    type: "tags",
    name: "flammable",
    description: "burns",
    color: "#f1c40f",
  },
  {
    immutable_id: "t2",
    type: "tags",
    name: "global-tag",
    description: null,
    color: null,
  },
];

function mountTable(role) {
  const store = createStore({
    state() {
      return {
        currentUserID: "self",
        currentUserRole: role,
        datatablePaginationSettings: {
          tags: { page: 0, rows: 20 },
        },
        tag_list: TAGS,
      };
    },
  });

  cy.mount(TagManagementTable, {
    global: {
      plugins: [store, PrimeVue],
      components: {
        StyledTooltip,
      },
    },
  });
}

describe("TagManagementTable Component Tests", () => {
  it("renders the expected (scope-free) columns", () => {
    mountTable("admin");
    const headers = ["", "Tag", "Description", "Actions"];
    cy.get(".p-datatable-column-header-content").should("have.length", headers.length);
    cy.get(".p-datatable-column-header-content").each((header, index) => {
      cy.wrap(header).should("contain.text", headers[index]);
    });
  });

  it("displays a badge per tag from the store", () => {
    mountTable("admin");
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(0)
      .within(() => {
        cy.get("td").eq(1).find(".badge").should("contain.text", "flammable");
      });
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => {
        cy.get("td").eq(1).find(".badge").should("contain.text", "global-tag");
      });
  });

  it("shows the create button and Edit/Delete on every tag for an admin", () => {
    mountTable("admin");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.get('button[title="Edit tag"]').should("have.length", TAGS.length);
    cy.get('button[title="Delete tag"]').should("have.length", TAGS.length);
  });

  it("hides create/edit/delete controls for a non-admin", () => {
    mountTable("user");
    cy.get('[data-testid="add-tag-button"]').should("not.exist");
    cy.get('button[title="Edit tag"]').should("not.exist");
    cy.get('button[title="Delete tag"]').should("not.exist");
  });
});
