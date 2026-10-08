import { createRouter, createMemoryHistory, RouterView } from "vue-router";
import { createStore } from "vuex";

import Settings from "@/views/Settings.vue";
import { DialogService } from "@/services/DialogService";

let mountedSettings;

function mountSettings(path, { tagsEnabled = true, accountHasChanges } = {}) {
  const store = createStore({
    state: {
      serverInfo: { features: { tags: tagsEnabled } },
    },
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/settings", name: "settings", component: Settings },
      { path: "/samples", name: "samples", component: { template: "<div />" } },
      {
        path: "/tags",
        name: "tags",
        redirect: { name: "settings", query: { section: "tags" } },
      },
    ],
  });

  router.push(path);
  cy.wrap(router.isReady()).then(() => {
    const accountSettingsStub =
      accountHasChanges === undefined
        ? true
        : {
            template: "<div />",
            data: () => ({ hasChanges: accountHasChanges }),
          };

    cy.mount(
      { components: { RouterView }, template: "<RouterView />" },
      {
        global: {
          plugins: [store, router],
          stubs: {
            Navbar: true,
            AccountSettings: accountSettingsStub,
            TagManagementTable: true,
          },
        },
      },
    ).then(({ wrapper }) => {
      mountedSettings = wrapper;
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

  it("leaves without prompting when the account form is unchanged", () => {
    const confirm = cy.stub(DialogService, "confirm").resolves(false);
    const router = mountSettings("/settings", { accountHasChanges: false });

    cy.then(() => router.push("/samples"));
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/samples");
      expect(confirm).not.to.have.been.called;
    });
  });

  it("stays on Settings when leaving with unsaved account changes is cancelled", () => {
    const confirm = cy.stub(DialogService, "confirm").resolves(false);
    const router = mountSettings("/settings", { accountHasChanges: true });

    cy.then(() => router.push("/samples"));
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings");
      expect(confirm).to.have.been.calledOnceWith({
        title: "Unsaved Changes",
        message: "You have unsaved changes. Leave without saving?",
        type: "warning",
        confirmButtonText: "Leave",
        cancelButtonText: "Stay",
      });
    });
  });

  it("leaves Settings when discarding unsaved account changes is confirmed", () => {
    cy.stub(DialogService, "confirm").resolves(true).as("confirmLeave");
    const router = mountSettings("/settings", { accountHasChanges: true });

    cy.then(() => router.push("/samples"));
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/samples");
    });
    cy.get("@confirmLeave").should("have.been.calledOnce");
  });

  it("only prevents browser unload when the account form has unsaved changes", () => {
    mountSettings("/settings", { accountHasChanges: false });

    cy.window().then((win) => {
      const event = new win.Event("beforeunload", { cancelable: true });
      win.dispatchEvent(event);
      expect(event.defaultPrevented).to.be.false;
    });

    cy.then(() => mountedSettings.unmount());
    mountSettings("/settings", { accountHasChanges: true });

    cy.window().then((win) => {
      const event = new win.Event("beforeunload", { cancelable: true });
      win.dispatchEvent(event);
      expect(event.defaultPrevented).to.be.true;
    });
  });

  it("removes the browser unload listener when Settings is unmounted", () => {
    cy.window().then((win) => {
      cy.spy(win, "removeEventListener").as("removeEventListener");
    });
    mountSettings("/settings", { accountHasChanges: true });

    cy.then(() => mountedSettings.unmount());
    cy.get("@removeEventListener").should(
      "have.been.calledWith",
      "beforeunload",
      Cypress.sinon.match.func,
    );
  });
});
