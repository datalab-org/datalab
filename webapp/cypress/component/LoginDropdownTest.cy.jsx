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

  it("keeps the user list available after a failed login", () => {
    cy.intercept("GET", "**/login/testing-passwordless/users", {
      users: [
        {
          username: "alice",
          display_name: "Alice Test User",
          role: "manager",
          account_status: "active",
        },
        {
          username: "bob",
          display_name: "Bob Test User",
          role: "user",
          account_status: "active",
        },
      ],
    });
    cy.intercept("POST", "**/login/testing-passwordless", {
      statusCode: 500,
      delay: 100,
    }).as("login");
    mountLoginDropdown();

    cy.get('[data-testid="testing-passwordless-open"]').click();
    cy.contains("button", "Alice Test User").click();
    cy.get('[data-testid="testing-passwordless-users"] button').should("be.disabled");
    cy.wait("@login").its("request.body.username").should("equal", "alice");

    cy.get('[data-testid="testing-passwordless-error"]')
      .should("be.visible")
      .and("contain", "Unable to log in as that test user");
    cy.contains("Alice Test User").should("be.visible");
    cy.contains("button", "Bob Test User").should("be.enabled").click();
    cy.wait("@login").its("request.body.username").should("equal", "bob");
  });
});
