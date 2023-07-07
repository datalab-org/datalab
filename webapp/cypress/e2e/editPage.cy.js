const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

describe("Edit Page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  // afterEach( () => {
  //  cy.expect(consoleSpy).not.to.be.called
  // });

  it("Loads the main page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Samples").should("exist");
    cy.findByText("Add an item").should("exist");
    cy.findByText("# of blocks").should("exist");
    cy.wait(1000).then((x) => {
      cy.contains("Server Error. Sample list not retreived.").should("not.exist");
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("Adds a valid sample", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("ID:").type("editable_sample");
    cy.findByLabelText("Date Created:").type("1990-01-07T00:00");

    cy.findByLabelText("Name:").type("This is a sample name");
    cy.contains("Submit").click();

    cy.findByText("editable_sample");
    cy.findByText("This is a sample name");
    cy.get("tr>td").eq(7).contains(0); // 0 blocks are present
  });

  it("Adds a second valid sample, to use as a component", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample");
    cy.findByLabelText("ID:").type("component1");
    cy.findByLabelText("Name:").type("This is a component");
    cy.contains("Submit").click();
  });

  it("Adds a third valid sample, to use as a component", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample");
    cy.findByLabelText("ID:").type("component2");
    cy.findByLabelText("Name:").type("This is another component");
    cy.contains("Submit").click();
  });

  it("Checks editing the sample edit page", () => {
    cy.findByText("editable_sample").click();
    cy.findByLabelText("Sample ID").should("have.value", "editable_sample");
    cy.findByLabelText("Name").should("have.value", "This is a sample name");
    cy.findByLabelText("Chemical formula").type("NaCoO2", { force: true });

    cy.findByText("Unsaved changes");
    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");
    cy.contains("Home").click();

    cy.findByText("editable_sample");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
    cy.get("tbody tr:nth-of-type(3)").contains("NaCoO2"); // sorta check the formula
  });

  it("adds a chemical formula to component1", () => {
    cy.findByText("component1").click();
    cy.findByLabelText("Chemical formula").type("Na2O", { force: true });

    cy.findByText("Unsaved changes");
    cy.wait(100).then(() => cy.get(".fa-save").click());
    cy.contains("Unsaved changes").should("not.exist");
  });

  it("adds some synthesis information", () => {
    cy.findByText("editable_sample").click();
    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 2);
    cy.findByText("Unsaved changes");

    cy.get("#synthesis-information").contains("component1");
    cy.get("#synthesis-information").contains("Na2O");

    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();

    cy.get("#synthesis-information").contains("component2");

    cy.get("#synthesis-information tr:nth-of-type(1) td:nth-of-type(2)").type(10);
    cy.get("#synthesis-information tr:nth-of-type(1) td:nth-of-type(3)").clear().type("mL");
    cy.get("#synthesis-information tr:nth-of-type(2) td:nth-of-type(2)").type(0.001);
    cy.get("#synthesis-information tr:nth-of-type(2) td:nth-of-type(3)").clear().type("kg");

    // save the synthesis information and make sure unsaved changes goes away
    cy.contains("Unsaved changes");
    cy.wait(100).then(() => cy.get(".fa-save").click());
    cy.contains("Unsaved changes").should("not.exist");

    cy.get("#synthesis-information tr:nth-of-type(2) td:nth-of-type(3) input")
      .clear()
      .type("pints");
    cy.contains("Unsaved changes");
    cy.wait(100).then(() => cy.get(".fa-save").click());
    cy.contains("Unsaved changes").should("not.exist");

    cy.reload();

    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      10
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "mL"
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      0.001
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(3) input").should(
      "have.value",
      "pints"
    );
  });

  it("deletes synthesis components and re-adds them", () => {
    cy.findByText("editable_sample").click();
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) .close").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 2);
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      0.001
    );
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "pints"
    );

    cy.get("#synthesis-information tbody > tr:nth-of-type(1) .close").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 1);

    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 2);
    cy.get("#synthesis-information").contains("component2");
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      ""
    ); // should be reset, not a previous value

    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 3);
    cy.get("#synthesis-information").contains("component1");
    cy.get("#synthesis-information").contains("Na2O");
    cy.get("#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      ""
    ); // should be reset, not a previous value
  });

  it("tries to add a non-numeric value into quantity", () => {
    cy.findByText("editable_sample").click();
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input").type(
      "100.001"
    );
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border"
    ).should("not.exist");
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input")
      .clear()
      .type("1");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border"
    ).should("not.exist");
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input")
      .clear()
      .type("word");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border"
    ).should("exist");

    cy.get("#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input")
      .clear()
      .type("$");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input.red-border"
    ).should("exist");

    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input")
      .clear()
      .type("1");
    cy.get("#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input")
      .clear()
      .type("1");
  });

  it("Add some blocks to the sample and checks unsaved warning behavior", () => {
    cy.findByText("editable_sample").click();
    cy.findByLabelText("Sample ID").should("have.value", "editable_sample");
    cy.findByLabelText("Name").should("have.value", "This is a sample name");

    cy.findByText("Add a block").click();
    cy.get(".dropdown-menu").within(() => {
      cy.findByText("Comment").click();
    });

    cy.contains("Unsaved changes").should("not.exist");

    cy.findByText("Add a block").click();
    cy.get(".dropdown-menu").within(() => {
      cy.findByText("Comment").click();
    });

    cy.contains("Unsaved changes").should("not.exist");

    cy.get(".datablock-content div").eq(0).type("the first comment box");
    cy.contains("Unsaved changes");

    // click update block icon and make sure unsaved changes warning goes away
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(0).click();
    cy.contains("Unsaved changes").should("not.exist");
    cy.get(".datablock-content div").eq(0).contains("the first comment box");

    cy.get(".datablock-content div").eq(0).type("The first comment box; further changes.");
    cy.contains("Unsaved changes");

    cy.get(".datablock-content div").eq(1).type("The second comment box");
    cy.contains("Unsaved changes");
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(1).click();
    cy.wait(500).then(() => {
      cy.contains("Unsaved changes"); // unsaved changes warning should still exist since first block is still edited
    });
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(0).click();
    cy.contains("Unsaved changes").should("not.exist");

    cy.get(".datablock-content div").eq(1).type("The second comment box; further changes");
    cy.findByLabelText("Name").type("name change");
    cy.contains("Unsaved changes");

    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");

    cy.findByText("Home").click();
    cy.get("[data-testid=sample-table] tr:nth-of-type(3) > td:nth-of-type(8)").contains(2); // 2 blocks are present
  });

  it("cleanup: delete the samples", () => {
    cy.findByText("editable_sample")
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });

    cy.findByText("component1")
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });

    cy.findByText("component2")
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });
  });
});
