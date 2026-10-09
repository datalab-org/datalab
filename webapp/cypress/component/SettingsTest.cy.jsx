import { createRouter, createMemoryHistory, RouterView } from "vue-router";
import { createStore } from "vuex";

import Settings from "@/views/Settings.vue";
import { DialogService } from "@/services/DialogService";
import applicationStore from "@/store/index.js";
import { routes as applicationRoutes } from "@/router/index.js";

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
    ],
  });

  const accountSettingsStub =
    accountHasChanges === undefined
      ? true
      : {
          template: "<div />",
          data: () => ({ hasChanges: accountHasChanges }),
        };

  cy.mount(RouterView, {
    global: {
      plugins: [store, router],
      stubs: {
        Navbar: true,
        AccountSettings: accountSettingsStub,
        TagManagementTable: true,
      },
    },
  }).then(({ wrapper }) => {
    mountedSettings = wrapper;
  });
  cy.then(() => router.push(path));

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

  it("preserves an unsaved profile draft while viewing Tag management", () => {
    const confirm = cy.stub(DialogService, "confirm").resolves(false);
    const router = mountSettings("/settings", { accountHasChanges: true });

    cy.contains("button", "Tag management").click();
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings?section=tags");
      expect(confirm).not.to.have.been.called;
    });

    cy.contains("button", "Account").click();
    cy.then(() => router.push("/samples"));
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings");
      expect(confirm).to.have.been.calledOnce;
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
        message: "Your profile has unsaved changes. Leave without saving?",
        type: "warning",
        confirmButtonText: "Leave",
        cancelButtonText: "Stay",
      });
    });
  });

  it("leaves Settings when leaving with unsaved account changes is confirmed", () => {
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

  it("stacks navigation above the content on narrow screens", () => {
    cy.viewport(575, 667);
    mountSettings("/settings");

    cy.get(".settings-container")
      .should("have.class", "flex-column")
      .and("have.class", "flex-md-row");
    cy.get("[data-testid='settings-table'] ul").should("have.css", "display", "flex");
    cy.get("[data-testid='settings-table']").should("have.css", "border-right-width", "0px");
    cy.get(".settings-container").should(($container) => {
      expect($container[0].scrollWidth).to.be.at.most($container[0].clientWidth);
    });
  });
});

describe("Settings routes", () => {
  function createApplicationRouter() {
    return createRouter({ history: createMemoryHistory(), routes: applicationRoutes });
  }

  afterEach(() => {
    applicationStore.commit("setServerInfo", null);
  });

  it("loads server metadata before resolving a cold Settings route", () => {
    applicationStore.commit("setServerInfo", null);
    cy.intercept("GET", "**/info", {
      body: { data: { attributes: { features: { tags: true } } } },
    }).as("getServerInfo");
    const router = createApplicationRouter();

    cy.then(() => router.push("/settings?section=tags"));
    cy.wait("@getServerInfo");
    cy.then(() => {
      expect(router.currentRoute.value.fullPath).to.equal("/settings?section=tags");
      expect(applicationStore.state.serverInfo.features.tags).to.be.true;
    });
  });
});
