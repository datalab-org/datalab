let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

describe("Sample table page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  // afterEach( () => {
  // 	cy.expect(consoleSpy).not.to.be.called
  // });

  it("Loads the main page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Samples").should("exist");
    cy.findByText("Add a sample").should("exist");
    cy.findByText("# of blocks").should("exist");

    // Ensure no error messages or console errors. The wait is necessary so that
    // the assertion does not run before the server has had
    // time to respond.
    // Can we wait for the server response instead of hard-coding
    // a wait time in ms?
    cy.wait(1000).then((x) => {
      cy.contains("Server Error. Sample list not retreived.").should("not.exist");
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("Adds a valid sample", () => {
    cy.findByText("Add a sample").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("Sample ID:").type("12345678910");
    cy.findByLabelText("Date Created:").type("1990-01-07");

    cy.findByLabelText("Sample Name:").type("This is a sample name");
    cy.findByText("Submit").click();
  });
});
