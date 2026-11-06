import Admin from "@/views/Admin.vue";
import AdminDisplay from "@/components/AdminDisplay.vue";
import { invalidateCurrentUserCache } from "@/server_fetch_utils.js";

describe("Admin view", () => {
  function mountAdmin(role) {
    invalidateCurrentUserCache();
    cy.intercept("GET", "**/get-current-user/", {
      body: {
        immutable_id: "111111111111111111111111",
        display_name: "Test User",
        role,
        account_status: "active",
      },
    }).as("getUser");

    cy.mount(Admin, {
      global: {
        stubs: {
          Navbar: true,
          AdminDisplay: true,
        },
      },
    });
    cy.wait("@getUser");
  }

  it("highlights the selected admin section", () => {
    mountAdmin("admin");

    cy.get("h1").should("contain.text", "Administration");
    cy.contains("button", "Users").should("have.class", "selected");
    cy.contains("button", "Groups").click();
    cy.contains("button", "Groups").should("have.class", "selected");
    cy.contains("button", "Users").should("not.have.class", "selected");
  });

  it("uses the responsive sidebar layout", () => {
    mountAdmin("admin");

    cy.get(".admin-container").should("have.class", "flex-column").and("have.class", "flex-md-row");
  });

  it("does not render administration controls for a non-admin user", () => {
    mountAdmin("user");

    cy.contains("You do not have permission to access this page.").should("be.visible");
    cy.get('[data-testid="admin-table"]').should("not.exist");
    cy.get("admin-display-stub").should("not.exist");
  });

  it("keeps administration content within a narrow viewport", () => {
    cy.viewport(375, 667);
    cy.mount(AdminDisplay, {
      props: { selectedItem: "Users" },
      global: { stubs: { UserTable: true } },
    });

    cy.get(".admin-display").should(($display) => {
      expect($display[0].scrollWidth).to.be.at.most($display[0].clientWidth);
      expect($display[0].getBoundingClientRect().right).to.be.at.most(
        $display[0].parentElement.getBoundingClientRect().right,
      );
    });
  });
});
