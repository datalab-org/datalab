const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

describe("Sample table page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  // afterEach( () => {
  //  cy.expect(consoleSpy).not.to.be.called
  // });

  it("Loads the main page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Samples").should("exist");
    cy.findByText("Add a sample").should("exist");
    cy.findByText("# of blocks").should("exist");
    cy.wait(1000).then((x) => {
      cy.contains("Server Error. Sample list not retreived.").should("not.exist");
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("Adds a valid sample", () => {
    cy.findByText("Add a sample").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("Sample ID:").type("editable_sample");
    cy.findByLabelText("Date Created:").type("1990-01-07T00:00");

    cy.findByLabelText("Sample Name:").type("This is a sample name");
    cy.contains("Submit").click();

    cy.findByText("editable_sample");
    cy.findByText("This is a sample name");
    cy.get("tr>td").eq(5).contains(0); // 0 blocks are present
  });

  it("Checks editing the sample edit page", () => {
    cy.findByText("editable_sample").click();
    cy.findByLabelText("Sample ID").should("have.value", "editable_sample");
    cy.findByLabelText("Name").should("have.value", "This is a sample name");
    cy.findByLabelText("Chemical formula").type("NaCoO2", { force: true });
    cy.findByText("Unsaved changes");
    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");
  });

  it("verifies the sample table after editing the sample", () => {
    cy.findByText("editable_sample");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
    cy.get("tr>td").eq(2).contains("Na"); // sorta check the formula
    cy.get("tr>td").eq(2).contains("2"); // sorta check the formula
    cy.get("tr>td").eq(5).contains(0); // 0 blocks are present
  });

  it("Add some blocks to the sample", () => {
    cy.findByText("editable_sample").click();
    cy.findByLabelText("Sample ID").should("have.value", "editable_sample");
    cy.findByLabelText("Name").should("have.value", "This is a sample name");

    cy.findByText("Add a block").click();
    cy.get(".dropdown-menu").within(() => {
      cy.findByText("Comment").click();
    });

    cy.findByText("Add a block").click();
    cy.get(".dropdown-menu").within(() => {
      cy.findByText("Comment").click();
    });

    cy.findByText("Unsaved changes");
    cy.wait(100).then(() => cy.get(".fa-save").click());
    cy.contains("Unsaved changes").should("not.exist");

    cy.get(".datablock-content div").eq(0).type("The first comment box");
    cy.get(".datablock-content div").eq(1).type("The second comment box");

    cy.findByText("Home").click();
    cy.get("tr>td").eq(5).contains(2); // 2 blocks are present
  });

  it("cleanup: delete the sample", () => {
    cy.findByText("editable_sample")
      .parent("tr")
      .within(() => {
        cy.get("button.close").click();
      });
  });
});
