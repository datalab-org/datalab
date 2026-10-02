import Admin from "@/views/Admin.vue";
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

    cy.contains("button", "Users").should("have.class", "selected");
    cy.contains("button", "Groups").click();
    cy.contains("button", "Groups").should("have.class", "selected");
    cy.contains("button", "Users").should("not.have.class", "selected");
  });

  it("does not render administration controls for a non-admin user", () => {
    mountAdmin("user");

    cy.contains("You do not have permission to access this page.").should("be.visible");
    cy.get('[data-testid="admin-table"]').should("not.exist");
    cy.get("admin-display-stub").should("not.exist");
  });
});
