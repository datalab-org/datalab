import { createStore } from "vuex";
import "bootstrap/dist/css/bootstrap.css";

import LoginDropdown from "@/components/LoginDropdown.vue";

function mountLoginDropdown({ enabled = true } = {}) {
  const store = createStore({
    state: {
      serverInfo: {
        features: {
          auth_mechanisms: {
            email: true,
            github: true,
            unsafe_testing_passwordless_login: enabled,
          },
        },
      },
    },
  });
  cy.mount(LoginDropdown, {
    global: { plugins: [store] },
  });
}

describe("LoginDropdown unsafe passwordless test login", () => {
  it("does not expose test users when disabled", () => {
    mountLoginDropdown({ enabled: false });

    cy.get('[data-testid="testing-passwordless-open"]').should("not.exist");
    cy.contains("Alice Test User").should("not.exist");
  });

  it("lists configured test users when enabled", () => {
    cy.intercept("GET", "**/login/testing-passwordless/users", {
      users: [
        {
          username: "alice",
          display_name: "Alice Test User",
          role: "manager",
          account_status: "active",
        },
      ],
    }).as("testUsers");
    mountLoginDropdown();

    cy.get('[data-testid="testing-passwordless-open"]').click();
    cy.wait("@testUsers");
    cy.contains("Alice Test User").should("be.visible");
  });
});
