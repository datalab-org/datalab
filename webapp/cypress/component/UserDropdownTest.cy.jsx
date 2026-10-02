import { createRouter, createMemoryHistory } from "vue-router";
import { createStore } from "vuex";

import UserDropdown from "@/components/UserDropdown.vue";

function mountDropdown(role) {
  const store = createStore({
    state: {
      currentUserIsUnverified: false,
      hasUnverifiedUser: false,
      adminSuperUserMode: false,
    },
    getters: {
      getCurrentUserIsUnverified: (state) => state.currentUserIsUnverified,
      getHasUnverifiedUser: (state) => state.hasUnverifiedUser,
      isAdminSuperUserModeActive: (state) => state.adminSuperUserMode,
    },
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/settings", component: { template: "<div />" } },
      { path: "/admin", component: { template: "<div />" } },
    ],
  });

  cy.mount(UserDropdown, {
    global: { plugins: [store, router] },
    props: { user: { role } },
  });
}

describe("UserDropdown", () => {
  it("links every user to the settings page", () => {
    mountDropdown("user");

    cy.contains("a", "Settings").should("have.attr", "href", "/settings");
    cy.contains("a", "Administration").should("not.exist");
    cy.contains("a", "Logout").should("exist");
  });

  it("keeps the admin link for administrators", () => {
    mountDropdown("admin");

    cy.contains("a", "Settings").should("have.attr", "href", "/settings");
    cy.contains("a", "Administration").should("have.attr", "href", "/admin");
  });
});
