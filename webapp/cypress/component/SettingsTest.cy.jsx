import { createRouter, createMemoryHistory } from "vue-router";
import { createStore } from "vuex";

import Settings from "@/views/Settings.vue";

function mountSettings(path, { tagsEnabled = true } = {}) {
  const store = createStore({
    state: {
      serverInfo: { features: { tags: tagsEnabled } },
    },
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/settings", name: "settings", component: Settings },
      {
        path: "/tags",
        name: "tags",
        redirect: { name: "settings", query: { section: "tags" } },
      },
    ],
  });

  router.push(path);
  cy.wrap(router.isReady()).then(() => {
    cy.mount(Settings, {
      global: {
        plugins: [store, router],
        stubs: {
          Navbar: true,
          AccountSettings: true,
          TagManagementTable: true,
        },
      },
    });
  });

  return router;
}

describe("Settings view", () => {
  it("opens account settings by default", () => {
    mountSettings("/settings");

    cy.get('[data-testid="settings-table"]').should("contain.text", "Settings");
    cy.contains("button", "Account")
      .should("have.class", "selected")
      .and("have.css", "text-decoration-line", "underline");
    cy.get("account-settings-stub").should("not.have.css", "display", "none");
    cy.get("tag-management-table-stub").should("not.exist");
  });

  it("navigates between account and tag management settings", () => {
    const router = mountSettings("/settings");

    cy.contains("button", "Tag management").click();
    cy.contains("button", "Tag management").should("have.class", "selected");
    cy.get("tag-management-table-stub").should("exist");
    cy.get("account-settings-stub").should("have.css", "display", "none");
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings?section=tags");
    });

    cy.contains("button", "Account").click();
    cy.contains("button", "Account").should("have.class", "selected");
    cy.get("account-settings-stub").should("not.have.css", "display", "none");
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings");
    });
  });

  it("redirects the legacy tags route and opens tag management", () => {
    const router = mountSettings("/tags");

    cy.contains("button", "Tag management").should("have.class", "selected");
    cy.get("tag-management-table-stub").should("exist");
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings?section=tags");
    });
  });

  it("hides tag management when tags are disabled", () => {
    mountSettings("/settings", { tagsEnabled: false });

    cy.contains("button", "Account").should("exist");
    cy.contains("button", "Tag management").should("not.exist");
  });

  it("normalizes an unavailable tags section to account settings", () => {
    const router = mountSettings("/settings?section=tags", { tagsEnabled: false });

    cy.get("account-settings-stub").should("not.have.css", "display", "none");
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings");
    });
  });

  it("preserves the account component while navigating between settings sections", () => {
    mountSettings("/settings");

    let accountSettingsElement;
    cy.get("account-settings-stub").then(($settings) => {
      accountSettingsElement = $settings[0];
    });
    cy.contains("button", "Tag management").click();
    cy.contains("button", "Account").click();

    cy.get("account-settings-stub").should(($settings) => {
      expect($settings[0]).to.equal(accountSettingsElement);
    });
  });
});
