// Smoke test for the collection page (CollectionPage.vue) and its responsive navbar.
// Needs the dev server (:8080) and API (:5001) running, like the other e2e specs.

const collectionId = "test_collection_smoke";

let consoleSpy; // tracks anything written to console.error during the test
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

before(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
  cy.visit("/collections");
  cy.removeAllTestCollections([collectionId], false);
  cy.createCollection(collectionId, "Smoke test collection");
});

after(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
  cy.visit("/collections");
  cy.removeAllTestCollections([collectionId], false);
});

describe("Collection page", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
  });

  it("loads the collection page and navbar without console errors", () => {
    cy.visit(`/collections/${collectionId}`);

    cy.get("nav.editor-navbar").should("be.visible");
    // brand shows the collection we navigated to
    cy.get(".navbar-brand-name").should("contain", collectionId);

    // navbar actions are present (labels stay in the DOM even when the
    // icon-only tier hides them visually)
    cy.get("nav.editor-navbar").within(() => {
      cy.findByText("Home").should("exist");
      cy.findByText("Export").should("exist");
      cy.findByText("Share").should("exist");
      cy.findByText("View JSON").should("exist");
    });

    cy.contains("Server Error").should("not.exist");
    cy.then(() => {
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("collapses to a hamburger and toggles the menu on mobile", () => {
    cy.viewport(390, 800);
    cy.visit(`/collections/${collectionId}`);

    // collapsed by default: the menu is hidden and the toggler is shown
    cy.get(".navbar-toggler").should("be.visible");
    cy.get("nav.editor-navbar").findByText("Home").should("not.be.visible");

    // opening the hamburger reveals the menu
    cy.get(".navbar-toggler").click();
    cy.get("nav.editor-navbar").findByText("Home").should("be.visible");
  });
});
