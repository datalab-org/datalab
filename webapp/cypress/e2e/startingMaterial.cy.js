const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

before(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
});

after(() => {
  cy.logout();
});

describe("Starting material table page - editable_inventory FALSE", () => {
  beforeEach(() => {
    cy.visit("/starting-materials");
  });

  it("Loads the Starting material page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Inventory").should("exist");
  });

  it("Add a starting material button isn't displayed", () => {
    cy.get('[data-testid="add-starting-material-button"]').should("not.exist");
  });
});
