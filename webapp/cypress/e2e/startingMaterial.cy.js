const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let item_ids = ["test_sm1", "test_sm2", "test_sm3", "123startingMaterial", "test_sm3_copy"];

before(() => {
  cy.visit("/starting-materials");
  cy.removeAllTestSamples(item_ids);
  cy.visit("/starting-materials").then(() => {
    cy.get("[data-testid='starting-material-table'] > tbody > tr").should("have.length", 0);
  });
});

after(() => {
  cy.visit("/starting-materials");
  cy.removeAllTestSamples(item_ids);
  cy.visit("/starting-materials").then(() => {
    cy.get("[data-testid='starting-material-table'] > tbody > tr").should("have.length", 0);
  });
});

describe("Starting material table page", () => {
  before(() => {
    Cypress.env("VUE_APP_EDITABLE_INVENTORY", "true");
  });

  beforeEach(() => {
    cy.visit("/starting-materials");
  });

  it("Loads the Starting material page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Inventory").should("exist");
    cy.findByText("Add a starting material").should("exist");
  });

  it("Adds some valid starting material entries", () => {
    cy.createStartingMaterial("test_sm1", "a scientific starting material");
    cy.verifyStartingMaterial("test_sm1", "a scientific starting material");

    cy.createStartingMaterial("test_sm2");
    cy.verifyStartingMaterial("test_sm2");

    cy.createStartingMaterial("test_sm3", "my inst", "1990-01-07T00:00:00");
    cy.verifyStartingMaterial("test_sm3", "my inst", "1990-01-07T00:00:00");

    cy.createStartingMaterial("123startingMaterial", null, "2005-04-03T00:00:00");
    cy.verifyStartingMaterial("123startingMaterial", null, "2005-04-03T00:00:00");
  });

  it("Checks if one of the starting material is in the database", () => {
    cy.request({ url: `${API_URL}/get-item-data/test_sm3`, failOnStatusCode: true })
      .its("body")
      .then((body) => {
        expect(body).to.have.property("item_id", "test_sm3");
        expect(body.item_data).to.have.property("item_id", "test_sm3");
        expect(body.item_data).to.have.property("name", "my inst");
        expect(body.item_data).to.have.property("date", "1990-01-07T00:00:00");
      });
  });

  it("Attempts to Add a starting material with the same name", () => {
    cy.findByText("Add a starting material").click();
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("test_sm3");
      cy.findByText("Submit").click();
    });

    cy.contains("already in use").should("exist");
    cy.get(".form-error a").contains("test_sm3");

    cy.get("[data-testid=create-item-form]").contains("Submit").should("be.disabled");
  });

  it("Deletes a starting material", function () {
    cy.deleteStartingMaterial(["test_sm2"]);
    cy.contains("test_sm2").should("not.exist");

    cy.request({ url: `${API_URL}/get-item-data/test_sm2`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });

  it("copies a starting material entry", () => {
    cy.findByText("Add a starting material").click();

    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("test_sm3_copy");
      cy.findByLabelText("(Optional) Copy from existing starting material:").type("test_sm3");
      cy.findByLabelText("(Optional) Copy from existing starting material:")
        .contains(".vs__dropdown-menu .badge", "test_sm3")
        .click();

      cy.findByLabelText("Name:"); //("COPY OF my inst")

      cy.findByText("Submit").click();
    });

    cy.verifyStartingMaterial("test_sm3_copy", "COPY OF my inst", null);
  });
});

describe("Starting material edit page", () => {
  beforeEach(() => {
    cy.visit("/starting-materials/");
  });

  it("Checks the equipment edit page", () => {
    cy.findByText("test_sm3").click();
    cy.wait(1000);
    cy.go("back");
    cy.verifyStartingMaterial("test_sm3", "my inst", "1990-01-07T00:00:00");
  });

  it("modifies some data in a starting material", () => {
    cy.findByText("test_sm3").click();
    cy.get('[id="item-description"]').type("this is a description of testB.");
    cy.findByLabelText("Date acquired").type("2000-01-01");
    cy.findByLabelText("Location").type("room 404");

    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");

    cy.get(".fa-save").click();
    cy.visit("/starting-materials");
    cy.verifyStartingMaterial("test_sm3", "my inst", "2000-01-01T00:00", "room 404");
  });
});

describe("Starting material table page - editable_inventory FALSE", () => {
  before(() => {
    Cypress.env("VUE_APP_EDITABLE_INVENTORY", "false");
  });

  beforeEach(() => {
    cy.visit("/starting-materials");
  });

  it("Does not allow adding starting materials", () => {
    cy.findByText("Add a starting material").click();
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("test_sm1");
      cy.findByText("Submit").click();
    });

    cy.get("[data-testid=create-item-form]").contains("Submit").should("be.disabled");
  });

  it("Does not allow modifying existing starting materials", () => {
    cy.findByText("test_sm3").click();
    cy.get('[id="item-description"]').should("not.exist");
  });
});
