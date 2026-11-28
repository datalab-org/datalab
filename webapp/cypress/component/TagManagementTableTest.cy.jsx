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
    // A user-defined tag owned by the current user ("self").
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
  {
    immutable_id: "t3",
    type: "tags",
    name: "group-tag",
    description: null,
    color: null,
    scope: "group",
    owner: "group-1",
    owner_name: "Demo Group",
  },
];

// The server decides who may edit/delete each tag (`can_manage` on each row of GET /tags):
// the owner of a user-defined tag, admins for global tags, and admins and the group's
// managers for group tags. Mirror that for the mounted role.
function tagsFor(role, { managesGroup = false } = {}) {
  const isAdmin = role === "admin";
  return TAGS.map((tag) => ({
    ...tag,
    can_manage:
      tag.scope === "user"
        ? tag.owner === "self"
        : tag.scope === "group"
          ? isAdmin || managesGroup
          : isAdmin,
  }));
}

function mountTable(role, options = {}) {
  const store = createStore({
    state() {
      return {
        currentUserID: "self",
        currentUserRole: role,
        datatablePaginationSettings: {
          tags: { page: 0, rows: 20 },
        },
        tag_list: tagsFor(role, options),
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
      .should("contain.text", "User-defined");
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
    // An admin owns the user-defined tag ("self") and manages the global tag, so both rows.
    mountTable("admin");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.get('button[title="Edit tag"]').should("have.length", TAGS.length);
    cy.get('button[title="Delete tag"]').should("have.length", TAGS.length);
  });

  it("lets a non-admin create tags and manage only their own user-defined tags", () => {
    // A non-admin can create (user-defined) tags, and manage their own user-defined tag,
    // but not the global tag (which only admins manage).
    mountTable("user");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.get('button[title="Edit tag"]').should("have.length", 1);
    cy.get('button[title="Delete tag"]').should("have.length", 1);
    // The controls sit on the user-defined (own) tag row, not the global one.
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(0)
      .within(() => cy.get('button[title="Edit tag"]').should("exist"));
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(1)
      .within(() => cy.get('button[title="Edit tag"]').should("not.exist"));
  });

  it("shows a group scope badge with the group's name", () => {
    mountTable("user");
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(2)
      .find('[data-testid="tag-scope-badge"]')
      .should("contain.text", "Group: Demo Group");
  });

  it("lets a group manager manage the group's tags", () => {
    // A non-admin managing the group can manage its tag as well as their own tag.
    mountTable("user", { managesGroup: true });
    cy.get('button[title="Edit tag"]').should("have.length", 2);
    cy.get(".p-datatable-tbody")
      .find("tr")
      .eq(2)
      .within(() => cy.get('button[title="Edit tag"]').should("exist"));
  });
});
