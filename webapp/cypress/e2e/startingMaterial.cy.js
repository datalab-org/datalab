const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

describe("Starting material table page - editable_inventory FALSE", () => {
  beforeEach(() => {
    cy.visit("/starting-materials");
  });

  it("Loads the Starting material page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Inventory").should("exist");
  });
});
