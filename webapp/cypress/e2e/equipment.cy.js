const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

let item_ids = ["test_e1", "test_e2", "test_e3", "123equipment", "test_e3_copy"];

before(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
});

after(() => {
  cy.logout();
});

before(() => {
  cy.visit("/equipment");
  cy.removeAllTestSamples(item_ids);
  cy.visit("/equipment").then(() => {
    cy.get("[data-testid='equipment-table'] > tbody > tr").should("have.length", 0);
  });
});

after(() => {
  cy.visit("/equipment");
  cy.removeAllTestSamples(item_ids);
  cy.visit("/equipment").then(() => {
    cy.get("[data-testid='equipment-table'] > tbody > tr").should("have.length", 0);
  });
});

describe("Equipment table page", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit("/equipment");
  });

  it("Loads the equipment page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Equipment").should("exist");
    cy.findByText("Add an item").should("exist");
    cy.findByText("Maintainers").should("exist");

    // Ensure no error messages or console errors. The wait is necessary so that
    // the assertion does not run before the server has had
    // time to respond.
    // Can we wait for the server response instead of hard-coding
    // a wait time in ms?
    cy.wait(100).then(() => {
      cy.contains("Server Error. Equipment list could not be retreived.").should("not.exist");
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("Adds some valid equipment entries", () => {
    cy.createEquipment("test_e1", "a scientific instrument");
    cy.verifyEquipment("test_e1", "a scientific instrument");

    cy.createEquipment("test_e2");
    cy.verifyEquipment("test_e2");

    cy.createEquipment("test_e3", "my inst", "1990-01-07T00:00:00");
    cy.verifyEquipment("test_e3", "my inst", "1990-01-07T00:00:00");

    cy.createEquipment("123equipment", null, "2005-04-03T00:00:00");
    cy.verifyEquipment("123equipment", null, "2005-04-03T00:00:00");
  });

  it("Checks if one of the equipment items is in the database", () => {
    cy.request({ url: `${API_URL}/get-item-data/test_e3`, failOnStatusCode: true })
      .its("body")
      .then((body) => {
        expect(body).to.have.property("item_id", "test_e3");
        expect(body.item_data).to.have.property("item_id", "test_e3");
        expect(body.item_data).to.have.property("name", "my inst");
        expect(body.item_data).to.have.property("date", "1990-01-07T00:00:00+00:00");
      });
  });

  it("Attempts to Add an item with the same name", () => {
    cy.findByText("Add an item").click();
    cy.get('[data-testid="create-equipment-form"]').within(() => {
      cy.findByText("Add equipment").should("exist");
      cy.findByLabelText("ID:").type("test_e3");
    });

    cy.contains("already in use").should("exist");
    cy.get(".form-error a").contains("test_e3");

    cy.get("[data-testid=create-equipment-form]").contains("Submit").should("be.disabled");
  });

  it("Deletes an item", function () {
    cy.deleteItems("equipment", ["test_e2"]);

    cy.contains("test_e2").should("not.exist");

    cy.request({ url: `${API_URL}/get-item-data/test_e2`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });

  it("copies an equipment entry", () => {
    cy.findByText("Add an item").click();

    cy.get('[data-testid="create-equipment-form"]').within(() => {
      cy.findByLabelText("ID:").type("test_e3_copy");
      cy.findByLabelText("(Optional) Copy from existing equipment:").type("test_e3");
      cy.findByLabelText("(Optional) Copy from existing equipment:")
        .contains(".vs__dropdown-menu .badge", "test_e3")
        .click();

      cy.findByLabelText("Name:"); //("COPY OF my inst")

      cy.findByText("Submit").click();
    });

    cy.verifyEquipment("test_e3_copy", "COPY OF my inst", null);
  });
});

describe("Equipment edit page", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit("/equipment");
  });

  it("Checks the equipment edit page", () => {
    cy.findByText("test_e3").click();
    cy.wait(1000);
    cy.go("back");
    cy.verifyEquipment("test_e3", "my inst", "1990-01-07T00:00:00");
  });

  it("modifies some data in a sample", () => {
    cy.findByText("test_e3").click();
    cy.findByLabelText("Description").type("this is a description of testB.");
    cy.findByLabelText("Date").type("2000-01-01T00:00");
    cy.findByLabelText("Location").type("room 101");

    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");

    cy.get(".fa-save").click();
    cy.visit("/equipment");
    cy.verifyEquipment("test_e3", "my inst", "2000-01-01T00:00", "room 101");
  });
});
