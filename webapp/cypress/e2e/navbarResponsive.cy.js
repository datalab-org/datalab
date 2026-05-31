// Visual check for the EditPage navbar across screen sizes.
// Screenshots land in cypress/screenshots/navbarResponsive.cy.js/.
// Run headed to watch it live:  npx cypress open --e2e   (pick this spec)
// Or headless for the screenshots: npx cypress run --spec cypress/e2e/navbarResponsive.cy.js
// Needs the dev server (:8080) and API (:5001) running, like the other e2e specs.

const itemId = "navbar_responsive_demo";
// A deliberately long name so the brand has something to truncate.
const longName = "A deliberately very long sample name to exercise navbar truncation";

// width -> short label, ordered small to large. Covers each breakpoint we care about:
// 575.98 (sm), 767.98 (md/hamburger), 768-991 (icon-only tier), 991.98/992 (lg, type appears).
const widths = [360, 480, 576, 700, 768, 880, 960, 992, 1100, 1280, 1440];
const height = 800;

describe("EditPage navbar — responsive", () => {
  before(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit("/");
    cy.removeAllTestSamples([itemId], false);
    cy.createSample(itemId, longName);
  });

  after(() => {
    cy.visit("/");
    cy.removeAllTestSamples([itemId], false);
  });

  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit(`/edit/${itemId}`);
    // wait until the navbar has rendered the item before measuring/snapping
    cy.get("nav.editor-navbar").should("be.visible");
  });

  widths.forEach((w) => {
    it(`renders at ${w}px wide`, () => {
      cy.viewport(w, height);

      // The item type prefix should only appear at >= xl (1200px),
      // and the item name must always be present.
      cy.get(".navbar-brand-name").should("be.visible");
      if (w >= 1200) {
        cy.get(".navbar-brand-type").should("be.visible");
      } else {
        cy.get(".navbar-brand-type").should("not.be.visible");
      }

      cy.get("nav.editor-navbar").screenshot(`navbar-${String(w).padStart(4, "0")}`);
    });
  });

  it("add-a-block dropdown closes on outside click (desktop)", () => {
    cy.viewport(1280, height);
    cy.get('[data-testid="add-block-button-top"]').click();
    cy.get('[data-testid="add-block-dropdown"]').should("be.visible");
    // click away from the dropdown
    cy.get("#topScrollPoint").click({ force: true });
    cy.get('[data-testid="add-block-dropdown"]').should("not.be.visible");
  });
});
