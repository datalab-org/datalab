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
    // A personal tag owned by the current user ("self").
    scope: "user",
    owner: "self",
  },
  {
    immutable_id: "t2",
    type: "tags",
    name: "global-tag",
    description: null,
    color: null,
    scope: "global",
    owner: null,
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
  it("renders the expected columns (including Scope)", () => {
    mountTable("admin");
    const headers = ["", "Tag", "Description", "Scope", "Actions"];
    cy.get(".p-datatable-column-header-content").should("have.length", headers.length);
    cy.get(".p-datatable-column-header-content").each((header, index) => {
      cy.wrap(header).should("contain.text", headers[index]);
    });
  });

  it("shows a scope badge per tag", () => {
    mountTable("admin");
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(0)
      .find('[data-testid="tag-scope-badge"]')
      .should("contain.text", "Personal");
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .find('[data-testid="tag-scope-badge"]')
      .should("contain.text", "Global");
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
    // An admin owns the personal tag ("self") and manages the global tag, so both rows.
    mountTable("admin");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.get('button[title="Edit tag"]').should("have.length", TAGS.length);
    cy.get('button[title="Delete tag"]').should("have.length", TAGS.length);
  });

  it("lets a non-admin create tags and manage only their own personal tags", () => {
    // A non-admin can create (personal) tags, and manage their own personal tag,
    // but not the global tag (which only admins manage).
    mountTable("user");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.get('button[title="Edit tag"]').should("have.length", 1);
    cy.get('button[title="Delete tag"]').should("have.length", 1);
    // The controls sit on the personal (own) tag row, not the global one.
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(0)
      .within(() => cy.get('button[title="Edit tag"]').should("exist"));
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => cy.get('button[title="Edit tag"]').should("not.exist"));
  });
});
