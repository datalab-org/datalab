// E2E coverage for the sharing flow: opening the SharingModal from the
// inline Creators/Groups widgets and from the navbar, switching tabs, and
// verifying the QR code / shareable link appear.

const item_ids = ["share_test_sample"];

before(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
  cy.visit("/");
  cy.removeAllTestSamples(item_ids, true);
  cy.createSample("share_test_sample", "Sample for sharing tests");
});

after(() => {
  cy.visit("/");
  cy.removeAllTestSamples(item_ids, true);
  cy.logout();
});

const modal = () => cy.get(".modal.show");

describe("Sharing modal", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit("/");
  });

  it("seeded sample is available", () => {
    cy.findByText("share_test_sample");
  });

  it("opens the sharing modal from the navbar and shows both tabs", () => {
    cy.findByText("share_test_sample").click();

    cy.get("nav").contains("a", "Share").click();

    modal().within(() => {
      // Default tab: Direct access.
      cy.get(".nav-tabs").contains("Direct access").should("have.class", "active");
      cy.get(".nav-tabs").contains("Sharing links & labels");
      cy.contains("People with access");
      cy.contains("Editor");
      cy.get(".fa-lock").should("exist");

      // Switch to the links tab — QR + shareable link render.
      cy.get(".nav-tabs").contains("Sharing links & labels").click();
      cy.get('[data-testid="shareable-link"]').should("be.visible");
      cy.get('[data-testid="shareable-link"] a').should("have.attr", "href");
    });

    modal().contains("button", "Done").click();
    cy.get(".modal.show").should("not.exist");
  });

  it("opens the sharing modal by clicking the inline Creators widget", () => {
    cy.findByText("share_test_sample").click();

    cy.get('[data-testid="toggleable-creators"]').click();

    modal().within(() => {
      cy.contains("People with access").should("be.visible");
    });

    modal().contains("button", "Done").click();
  });

  it("opens the sharing modal by clicking the inline Groups widget", () => {
    cy.findByText("share_test_sample").click();

    cy.get('[data-testid="toggleable-groups"]').click();

    modal().within(() => {
      cy.contains("Groups with access").should("be.visible");
    });

    modal().contains("button", "Done").click();
  });

  it("opens the UserSelect editor when entering Manage mode for People", () => {
    cy.findByText("share_test_sample").click();
    cy.get("nav").contains("a", "Share").click();

    // Two "Manage" buttons exist (People + Groups); take the first.
    modal().contains("button", "Manage").first().click();
    modal().find(".vs__dropdown-toggle").should("exist");

    // Click outside the dropdown (modal header is safe) to dismiss Manage
    // mode via OnClickOutside. Shadow equals current value so no confirm
    // dialog should fire.
    modal().find(".modal-header").click();
    modal().find(".vs__dropdown-toggle").should("not.exist");
    cy.contains("Update Permissions").should("not.exist");

    // Explicitly use the footer's primary Done button.
    modal().find(".modal-footer .btn-primary").click();
    cy.get(".modal.show").should("not.exist");
  });
});
