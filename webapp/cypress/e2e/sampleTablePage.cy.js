const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let item_ids = [
  "12345678910",
  "test1",
  "test2",
  "test3",
  "test4",
  "sdlkfjs",
  "w343t",
  "dfow4_112",
  "122.rwre",
  "56oer09gser9sdfd0s9dr333e",
  "7",
  "XX",
  "yyy",
  "testA",
  "testB",
  "testAcopy",
  "testBcopy",
  "testBcopy_copy",
  "component1",
  "component2",
  "component3",
  "component4",
];

let collection_ids = ["test_collection"];

before(() => {
  cy.cleanTestEnvironment({
    itemIds: item_ids,
    collectionIds: collection_ids,
  });
});

after(() => {
  cy.cleanTestEnvironment({
    itemIds: item_ids,
    collectionIds: collection_ids,
  });
});

describe("Sample table page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("Loads the main page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Samples").should("exist");
    cy.findByTestId("add-item-button").should("exist");
    cy.findByText("# of blocks").should("exist");

    cy.contains("Server Error. Sample list could not be retreived.").should("not.exist");
    cy.get("@consoleSpy").should("not.be.called");
  });

  it("Adds a valid sample", () => {
    cy.createSample("12345678910", "This is a sample name", "1990-01-07T00:00");
    cy.verifySample("12345678910", "This is a sample name", "1990-01-07T00:00");
  });

  it("Checks if the sample is in the database", () => {
    cy.request({ url: `${API_URL}/get-item-data/12345678910`, failOnStatusCode: true })
      .its("body")
      .then((body) => {
        expect(body).to.have.property("item_id", "12345678910");
        expect(body.item_data).to.have.property("item_id", "12345678910");
        expect(body.item_data).to.have.property("name", "This is a sample name");
        expect(body.item_data).to.have.property("date", "1990-01-07T00:00:00");
      });
  });

  it("Attempts to add an item with the same name", () => {
    cy.openAndWaitForModal("[data-testid=add-item-button]");
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("12345678910");
      cy.contains("already in use").should("exist");
      cy.get(".form-error a").contains("12345678910");
      cy.findByText("Submit").should("be.disabled");
    });
  });

  it("Deletes a sample", function () {
    cy.deleteSample("12345678910");

    cy.request({ url: `${API_URL}/get-item-data/12345678910`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });

  it("Adds a sample with an automatic ID", () => {
    const name = "sample with automatically generated id";
    const date = "2024-03-26T00:00";

    cy.createSample("irrelevant_id", name, date, true);

    cy.get('[data-testid="sample-table"]')
      .contains(name)
      .parents("tr")
      .find("td.table-item-id .formatted-item-name")
      .invoke("text")
      .as("createdId");

    cy.get("@createdId").then((createdId) => {
      expect(createdId).not.to.equal("irrelevant_id");
      cy.verifySample(createdId, name, date);
      cy.deleteSample(createdId);
    });
  });

  it("Adds several valid samples", () => {
    cy.createSample("test1");
    cy.verifySample("test1");

    cy.createSample("test2", "second sample name");
    cy.verifySample("test1");
    cy.verifySample("test2", "second sample name");

    cy.createSample("test3", "third sample name", "2006-04-25T00:00");
    cy.verifySample("test1");
    cy.verifySample("test2", "second sample name");
    cy.verifySample("test3", "third sample name", "2006-04-25T00:00");

    cy.createSample("test4");
    cy.verifySample("test1");
    cy.verifySample("test2", "second sample name");
    cy.verifySample("test3", "third sample name", "2006-04-25T00:00");
    cy.verifySample("test4");

    cy.deleteSample("test2");
    cy.contains("test2").should("not.exist");
    cy.contains("second sample name").should("not.exist");
    cy.verifySample("test1");
    cy.verifySample("test3", "third sample name", "2006-04-25T00:00");
    cy.verifySample("test4");

    cy.deleteSample("test1");
    cy.contains("test1").should("not.exist");
    cy.deleteSample("test4");
    cy.contains("test1").should("not.exist");
    cy.contains("test4").should("not.exist");

    const more_ids = [
      "sdlkfjs",
      "w343t",
      "dfow4_112",
      "122.rwre",
      "56oer09gser9sdfd0s9dr333e",
      "7",
      "XX",
      "yyy",
    ];
    more_ids.map((id) => cy.createSample(id));
    more_ids.map((id) => cy.verifySample(id));

    // check one of the pages to make sure it is generating properly
    cy.findByText("122.rwre").click();
    cy.wait(1000);
    cy.go("back");

    more_ids.map((id) => cy.verifySample(id));

    cy.wait(1000);

    more_ids.map((id) => cy.deleteSample(id));
    more_ids.map((id) => cy.contains(id).should("not.exist"));

    cy.deleteSample("test3");
    cy.contains("test3").should("not.exist");

    // make sure one of the pages is really deleted
    cy.request({ url: `${API_URL}/get-item-data/_122rwre`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });
});

describe.only("Advanced sample creation features", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds some valid samples", () => {
    cy.createSample("testA", "the first test sample");
    cy.createSample("testB", "the second test sample");
  });

  it("Adds a third sample copied from the first", () => {
    cy.openAndWaitForModal("[data-testid=add-item-button]");
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("testAcopy");
      cy.selectVsOption("copy-from-select", "testA", { dataTestId: true });
      cy.findByDisplayValue("COPY OF the first test sample").clear().type("a copied sample");
      cy.findByText("Submit").click();
    });
    cy.verifySample("testAcopy", "a copied sample");
  });

  it("deletes the first sample and makes sure the copy is still there", () => {
    cy.deleteSampleViaAPI("testA");
    cy.verifySample("testAcopy", "a copied sample");
  });

  it("makes some more items for testing as components", () => {
    cy.createSample("component1");
    cy.createSample("component2");
    cy.createSample("component3");
    cy.createSample("component4");
  });

  it("modifies some data in the second sample", () => {
    cy.findByText("testB").click();
    cy.findByLabelText("Description").type("this is a description of testB.");
    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");
    cy.expandIfCollapsed("[data-testid=synthesis-block]");
    cy.selectVsOption("synthesis-table", "component3", { dataTestId: true });

    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).type("30");

    cy.get("svg.add-row-button").click();
    cy.selectVsOption("synthesis-table", "component4", { dataTestId: true });

    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).type("100"); // eq(1) gets the second element that matches

    cy.findByLabelText("Procedure").type("a description of the synthesis here");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();
  });

  it("copies the second sample", () => {
    cy.openAndWaitForModal("[data-testid=add-item-button]");
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("testBcopy");
      cy.selectVsOption("copy-from-select", "testB", { dataTestId: true });
      cy.findByText("Submit").click();
    });
    cy.verifySample("testBcopy", "COPY OF the second test sample");
  });

  it("checks the edit page of the copied sample", () => {
    cy.findByText("testBcopy").click();
    cy.findByLabelText("Name").should("have.value", "COPY OF the second test sample");
    cy.findByText("this is a description of testB.");
    cy.findByText("a comment is added here.");
    cy.findByText("a description of the synthesis here");
    cy.findAllByText("component3");
    cy.findAllByText("component4");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "30");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
      .eq(0)
      .should("have.value", "100");
  });

  it("copies the copied sample, this time with additional components", () => {
    cy.openAndWaitForModal("[data-testid=add-item-button]");
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type("testBcopy_copy");

      cy.selectVsOption("copy-from-select", "testBcopy", { dataTestId: true });
      cy.selectVsOption("start-with-constituents", "component2", { dataTestId: true });
      cy.selectVsOption("start-with-constituents", "component3", { dataTestId: true });

      cy.findByText("Submit").click();
    });
    cy.verifySample("testBcopy_copy", "COPY OF COPY OF the second test sample");
  });
  it("checks the edit page of the copied sample with components", () => {
    cy.findByText("testBcopy_copy").click();
    cy.findByLabelText("Name").should("have.value", "COPY OF COPY OF the second test sample");
    cy.findByText("this is a description of testB.");
    cy.findByText("a comment is added here.");
    cy.findByText("a description of the synthesis here");
    cy.findAllByText("component3");
    cy.findAllByText("component4");
    cy.findAllByText("component2");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "30"); // eq(1) gets the second element that matches
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
      .eq(0)
      .should("have.value", "100"); // eq(1) gets the second element that matches
    cy.get("#synthesis-information tbody tr:nth-of-type(3) input").eq(0).should("have.value", ""); // eq(1) gets the second element that matches
  });
  it("selects a sample by checkbox, adds it to a new collection, then checks the collections page", () => {
    // Insert 'component4' into new collection called 'test_collection'
    let test_id = "component4";
    cy.selectItemCheckbox("sample", test_id);
    cy.get('[data-testid="selected-dropdown"]').click();
    cy.get('[data-testid="add-to-collection-button"]').click();

    cy.waitForModal();

    cy.findByLabelText("Insert into collection:").type("test_collection");
    cy.findByText('Create new collection: "test_collection"').click();
    cy.get('form[data-testid="add-to-collection-form"]').within(() => {
      cy.findByText("Submit").click();
    });
    // Visit collections page and look for 'test_collection'
    cy.visit("/collections");
    // Visit edit page of collection and check that the sample is there
    cy.get('[data-testid="search-input"]').type("test_collection");
    cy.findByText("test_collection").click();
    cy.findByText(test_id).should("exist");
  });
});
