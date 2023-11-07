const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

const TODAY = new Date().toISOString().slice(0, -8);

function getSubmitButton() {
  return cy.get("[data-testid=batch-modal-container]").contains("Submit");
}

function getBatchAddCell(row, column, additionalSelectors = "") {
  return cy.get(
    `[data-testid=batch-add-table] > tbody > tr:nth-of-type(${row}) > td:nth-of-type(${column}) ${additionalSelectors}`,
  );
}

function getBatchTemplateCell(column, additionalSelectors = "") {
  return cy.get(
    `[data-testid=batch-add-table-template] > tbody > td:nth-of-type(${column}) ${additionalSelectors}`,
  );
}

function getBatchAddError(row, additionalSelectors = "") {
  return cy.get(
    `[data-testid=batch-add-table] > tbody > tr:nth-of-type(${row}) + td ${additionalSelectors}`,
  );
}

function searchAndSelectItem(search_text, selector, delay = 100) {
  // searches in the dropdown for the first real item with the given name, looking for a badge
  // if click_plus, then also click the add row button before looking for the search bar
  cy.get("#synthesis-information").within(() => {
    cy.get("svg.add-row-button").click();
  });
  cy.get(selector).first().type(search_text);
  cy.wait(delay).then(() => {
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", search_text).click();
    });
  });
}

function createSample(sample_id, name = null, date = null) {
  cy.findByText("Add an item").click();
  cy.findByText("Add new sample").should("exist");
  cy.findByLabelText("ID:").type(sample_id);
  if (name) {
    cy.findByLabelText("Name:").type(name);
  }
  if (date) {
    cy.findByLabelText("Date Created:").type(date);
  }
  cy.contains("Submit").click();
}

function verifySample(sample_id, name = null, date = null) {
  if (date) {
    cy.get("[data-testid=sample-table]")
      .contains(sample_id)
      .parents("tr")
      .within(() => {
        cy.contains(date.slice(0, 8));
        if (name) {
          cy.contains(name);
        }
      });
  } else {
    cy.get("[data-testid=sample-table]")
      .contains(sample_id)
      .parents("tr")
      .within(() => {
        cy.contains(TODAY.split("T")[0]);
        if (name) {
          cy.contains(name);
        }
      });
  }
}

function deleteSample(sample_id, delay = 100) {
  cy.wait(delay).then(() => {
    cy.log("search for and delete: " + sample_id);
    var matchingIds = [];
    cy.get("[data-testid=sample-table]")
      .contains(sample_id)
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });
  });
}

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
    cy.findByText("Add an item").should("exist");
    cy.findByText("# of blocks").should("exist");

    // Ensure no error messages or console errors. The wait is necessary so that
    // the assertion does not run before the server has had
    // time to respond.
    // Can we wait for the server response instead of hard-coding
    // a wait time in ms?
    cy.wait(100).then((x) => {
      cy.contains("Server Error. Sample list not retreived.").should("not.exist");
      expect(consoleSpy).not.to.be.called;
    });
  });

  it("Adds a valid sample", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("ID:").type("12345678910");
    cy.findByLabelText("Date Created:").type("1990-01-07T00:00");

    cy.findByLabelText("Name:").type("This is a sample name");
    cy.contains("Submit").click();

    // check that the sample table is correctly populated
    cy.findByText("12345678910");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
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

  it("Checks the sample edit page", () => {
    cy.findByText("12345678910").click();
    cy.wait(1000);
    cy.go("back");
    cy.findByText("12345678910");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
  });

  it("Attempts to Add an item with the same name", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("ID:").type("12345678910");

    cy.contains("already in use").should("exist");
    cy.get(".form-error a").contains("12345678910");

    cy.contains("Submit").should("be.disabled");
  });

  it("Deletes a sample", function () {
    cy.get("tr#12345678910 button.close").click();
    cy.contains("12345678910").should("not.exist");
  });

  it("Attempts to go to the page of the deleted sample", function () {
    cy.request({ url: `${API_URL}/get-item-data/12345678910`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });

  it("Adds several valid samples", () => {
    createSample("test1");
    verifySample("test1");

    createSample("test2", "second sample name");
    verifySample("test1");
    verifySample("test2", "second sample name");

    createSample("test3", "third sample name", "2006-04-25T00:00");
    verifySample("test1");
    verifySample("test2", "second sample name");
    verifySample("test3", "third sample name", "2006-04-25T00:00");

    createSample("test4");
    verifySample("test1");
    verifySample("test2", "second sample name");
    verifySample("test3", "third sample name", "2006-04-25T00:00");
    verifySample("test4");

    deleteSample("test2");
    cy.contains("test2").should("not.exist");
    cy.contains("second sample name").should("not.exist");
    verifySample("test1");
    verifySample("test3", "third sample name", "2006-04-25T00:00");
    verifySample("test4");

    deleteSample("test1");
    cy.contains("test1").should("not.exist");
    deleteSample("test4");
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
    more_ids.map((id) => createSample(id));
    more_ids.map((id) => verifySample(id));

    // check one of the pages to make sure it is generating properly
    cy.findByText("122.rwre").click();
    cy.wait(1000);
    cy.go("back");

    more_ids.map((id) => verifySample(id));

    cy.wait(1000);

    more_ids.map((id) => deleteSample(id));
    more_ids.map((id) => cy.contains(id).should("not.exist"));

    deleteSample("test3");
    cy.contains("test3").should("not.exist");

    // make sure one of the pages is really deleted
    cy.request({ url: `${API_URL}/get-item-data/_122rwre`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
  });
});

describe("Advanced sample creation features", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds some valid samples", () => {
    createSample("testA", "the first test sample");
    createSample("testB", "the second test sample");
  });

  it("Adds a third sample copied from the first", () => {
    cy.findByText("Add an item").click();
    cy.findByLabelText("ID:").type("testAcopy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testA");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "testA").click();
    });
    cy.findByDisplayValue("COPY OF the first test sample").clear().type("a copied sample");
    cy.contains("Submit").click();
    verifySample("testAcopy", "a copied sample");
  });

  it("deletes the first sample and makes sure the copy is still there", () => {
    deleteSample("testA");
    verifySample("testAcopy", "a copied sample");
  });

  it("makes some more items for testing as components", () => {
    createSample("component1");
    createSample("component2");
    createSample("component3");
    createSample("component4");
  });

  it("modifies some data in the second sample", () => {
    cy.findByText("testB").click();
    cy.findByLabelText("Description").type("this is a description of testB.");
    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");
    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component3").click();
    });
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).type("30");

    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component4");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component4").click();
    });
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).type("100"); // eq(1) gets the second element that matches

    cy.findByLabelText("Procedure").type("a description of the synthesis here");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();

    /* ==== End Cypress Studio ==== */
  });

  it("copies the second sample", () => {
    cy.findByText("Add an item").click();
    cy.findByLabelText("ID:").type("testBcopy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "testB").click();
    });
    cy.contains("Submit").click();
    verifySample("testBcopy", "COPY OF the second test sample");
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
    cy.findByText("Add an item").click();
    cy.findByLabelText("ID:").type("testBcopy_copy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testBcopy");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "testBcopy").click();
    });

    cy.findByLabelText("(Optional) Start with constituents:").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component2").click();
    });
    cy.findByLabelText("(Optional) Start with constituents:").type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component3").click();
    });

    cy.contains("Submit").click();
    verifySample("testBcopy_copy", "COPY OF COPY OF the second test sample");
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

  it("deletes all samples", () => {
    [
      "testAcopy",
      "component1",
      "component2",
      "component3",
      "component4",
      "testBcopy_copy",
      "testBcopy",
      "testB",
    ].map((id) => {
      deleteSample(id);
    });
  });
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
      10,
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "mL",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      0.001,
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(3) input").should(
      "have.value",
      "pints",
    );
  });

  it("deletes synthesis components and re-adds them", () => {
    cy.findByText("editable_sample").click();
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) .close").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 2);
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      0.001,
    );
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "pints",
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
      "",
    ); // should be reset, not a previous value

    cy.get("svg.add-row-button").click();
    cy.get("#synthesis-information .vs__search").first().type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();
    cy.get("#synthesis-information tbody > tr").should("have.length", 3);
    cy.get("#synthesis-information").contains("component1");
    cy.get("#synthesis-information").contains("Na2O");
    cy.get("#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      "",
    ); // should be reset, not a previous value
  });

  it("tries to add a non-numeric value into quantity", () => {
    cy.findByText("editable_sample").click();
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input").type(
      "100.001",
    );
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border",
    ).should("not.exist");
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input")
      .clear()
      .type("1");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border",
    ).should("not.exist");
    cy.get("#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input")
      .clear()
      .type("word");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(1) td:nth-of-type(2) input.red-border",
    ).should("exist");

    cy.get("#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input")
      .clear()
      .type("$");
    cy.get(
      "#synthesis-information tbody > tr:nth-of-type(2) td:nth-of-type(2) input.red-border",
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

  it("deletes the samples (cleanup)", () => {
    ["editable_sample", "component1", "component2"].forEach((item_id) => {
      deleteSample(item_id);
    });

    cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
  });
});

describe("Batch sample creation", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds 3 valid samples", () => {
    cy.contains("Add batch of samples").click();
    getSubmitButton().should("be.disabled");
    cy.contains("Submit").should("be.disabled");
    getBatchAddCell(1, 1).type("testA");
    getBatchAddCell(2, 1).type("testB");
    getBatchAddCell(2, 2).type("this sample has a name");
    getSubmitButton().should("be.disabled");
    getBatchAddCell(3, 1).type("testC");
    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "testA");
    cy.get("[data-testid=batch-modal-container]").contains("a", "testB");
    cy.get("[data-testid=batch-modal-container]").contains("a", "testC");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("testA");
    verifySample("testB", "this sample has a name");
    verifySample("testC");

    deleteSample("testA");
    deleteSample("testB");
    deleteSample("testC");
  });

  it("adds two valid samples", () => {
    cy.contains("Add batch of samples").click();
    cy.findByLabelText("Number of rows:").clear().type(2);

    cy.contains("Submit").should("be.disabled");
    getBatchAddCell(1, 1).type("baseA");
    getBatchAddCell(2, 1).type("baseB");
    getBatchAddCell(2, 2).type("the name of baseB");
    getBatchAddCell(2, 3).type("1999-12-31T01:00");
    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB");
    cy.findAllByText("Successfully created.").should("have.length", 2);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("baseA");
    verifySample("baseB", "the name of baseB", "1999-12-31T01:00");
  });

  it("adds four base samples", () => {
    cy.contains("Add batch of samples").click();
    cy.findByLabelText("Number of rows:").clear().type(4);

    cy.contains("Submit").should("be.disabled");
    getBatchAddCell(1, 1).type("component1");
    getBatchAddCell(1, 2).type("this component has a name");
    getBatchAddCell(2, 1).type("component2");
    getBatchAddCell(3, 1).type("component3");
    getBatchAddCell(4, 1).type("component4");

    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "component1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component3");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component4");

    cy.findAllByText("Successfully created.").should("have.length", 4);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("component1", "this component has a name");
    verifySample("component2");
    verifySample("component3");
    verifySample("component4");
  });

  it("modifies some data in the first sample", () => {
    cy.findByText("baseA").click();
    cy.findByLabelText("Description").type("this is a description of baseA.");
    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();
  });

  it("modifies some data in the second sample", () => {
    cy.findByText("baseB").click();
    cy.findByLabelText("Description").type("this is a description of baseB.");
    cy.findByText("Add a block").click();
    cy.findByLabelText("Add a block").contains("Comment").click();
    cy.get(".datablock-content div").first().type("a comment is added here.");

    cy.findByLabelText("Procedure").type("a description of the synthesis here");

    cy.findByText("Add a block").click();
    cy.findByLabelText("Add a block").findByText("Comment").click();
    cy.get(".datablock-content").eq(1).type("a second comment is added here.");

    searchAndSelectItem("component3", "#synthesis-information .vs__search");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").first().type("30");

    searchAndSelectItem("component4", "#synthesis-information .vs__search");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).type("100");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();
  });

  it("makes samples copied from others", () => {
    cy.contains("Add batch of samples").click();
    getBatchAddCell(1, 1).type("baseA_copy");
    getBatchAddCell(1, 2).type("a copied sample");
    getBatchAddCell(1, 4, ".vs__search").type("BaseA");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseA").click();
    });
    cy.wait(100);

    getBatchAddCell(2, 1).type("baseB_copy");
    getBatchAddCell(2, 4, ".vs__search").type("BaseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });
    cy.wait(100);

    getBatchAddCell(3, 1).type("baseB_copy2");
    getBatchAddCell(3, 4, ".vs__search").type("BaseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });

    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy2");

    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("baseA_copy", "a copied sample");
    verifySample("baseB_copy");
    verifySample("baseB_copy2");
  });
  it("checks the copied samples", () => {
    // check the copied samples
    cy.contains("baseA_copy").click();
    cy.findByLabelText("Name").should("have.value", "a copied sample");
    cy.findByText("this is a description of baseA.");
    cy.findByText("a comment is added here.");
    cy.findByText("Home").click();

    cy.contains(/^baseB_copy$/).click();
    cy.findByText("this is a description of baseB.");
    cy.findByText("a comment is added here.");
    cy.findByText("a second comment is added here.");
    cy.findByText("a description of the synthesis here");
    cy.findAllByText("component3");
    cy.findAllByText("component4");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "30");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
      .eq(0)
      .should("have.value", "100");
    cy.findByText("Home").click();

    cy.findByText("baseB_copy2").click();
    cy.findByText("this is a description of baseB.");
    cy.findByText("a comment is added here.");
    cy.findByText("a second comment is added here.");
    cy.findByText("a description of the synthesis here");
    cy.findAllByText("component3");
    cy.findAllByText("component4");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "30");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
      .eq(0)
      .should("have.value", "100");
    cy.findByText("Home").click();
  });

  it("creates samples using components", () => {
    cy.contains("Add batch of samples").click();
    cy.findByLabelText("Number of rows:").clear().type(4);

    // sample with two components
    getBatchAddCell(1, 1).type("test101");
    getBatchAddCell(1, 2).type("sample with two components");
    getBatchAddCell(1, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component1").click();
    });
    getBatchAddCell(1, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component2").click();
    });

    // sample with two components, copied from a sample with no components
    getBatchAddCell(2, 1).type("test102");
    getBatchAddCell(2, 2).type(
      "sample with two components, copied from a sample with no components",
    );
    getBatchAddCell(2, 4, ".vs__search").type("baseA");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseA").click();
    });
    getBatchAddCell(2, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component1").click();
    });
    getBatchAddCell(2, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component2").click();
    });

    // sample with one components, copied from a sample with two components
    getBatchAddCell(3, 1).type("test103");
    getBatchAddCell(3, 2).type(
      "sample with one component, copied from a sample with two components",
    );
    getBatchAddCell(3, 4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });
    getBatchAddCell(3, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component1").click();
    });

    // sample with three components, copied from a sample with some of the same components
    getBatchAddCell(4, 1).type("test104");
    getBatchAddCell(4, 2).type(
      "sample with three components, copied from a sample with some of the same components",
    );
    getBatchAddCell(4, 4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });
    getBatchAddCell(4, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component2").click();
    });
    getBatchAddCell(4, 5, ".vs__search").type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component3").click();
    });
    getBatchAddCell(4, 5, ".vs__search").type("component4");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component4").click();
    });

    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "test101");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test102");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test103");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test104");

    cy.findAllByText("Successfully created.").should("have.length", 4);
    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
  });

  it("checks the created samples", () => {
    cy.contains("test101").click();
    cy.findByLabelText("Name").should("have.value", "sample with two components");
    cy.get("#synthesis-information table").contains("component1");
    cy.get("#synthesis-information table").contains("component2");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).should("have.value", "");
    cy.findByText("Home").click();

    cy.contains("test102").click();
    cy.findByLabelText("Name").should(
      "have.value",
      "sample with two components, copied from a sample with no components",
    );
    cy.contains("this is a description of baseA.");
    cy.get("#synthesis-information table").contains("component1");
    cy.get("#synthesis-information table").contains("component2");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).should("have.value", "");
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).should("have.value", "");
    cy.findByText("a comment is added here.");
    cy.findByText("Home").click();

    cy.contains("test103").click();
    cy.findByLabelText("Name").should(
      "have.value",
      "sample with one component, copied from a sample with two components",
    );
    cy.contains("this is a description of baseB.");
    cy.get("#synthesis-information table").contains("component1");
    cy.get("#synthesis-information table").contains("this component has a name");

    cy.get("#synthesis-information table").contains("component3");
    cy.get("#synthesis-information table").contains("component4");

    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      "30",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "g",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      "100",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(3) input").should(
      "have.value",
      "g",
    );

    cy.findByText("a comment is added here.");
    cy.findByText("a second comment is added here.");
    cy.findByText("Home").click();

    cy.contains("test104").click();
    cy.findByLabelText("Name").should(
      "have.value",
      "sample with three components, copied from a sample with some of the same components",
    );
    cy.contains("this is a description of baseB.");
    cy.get("#synthesis-information table").contains("component2");

    cy.get("#synthesis-information table").contains("component3");
    cy.get("#synthesis-information table").contains("component4");

    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(2) input").should(
      "have.value",
      "30",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(1) td:nth-of-type(3) input").should(
      "have.value",
      "g",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(2) input").should(
      "have.value",
      "100",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(2) td:nth-of-type(3) input").should(
      "have.value",
      "g",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(3) td:nth-of-type(2) input").should(
      "have.value",
      "",
    );
    cy.get("#synthesis-information tbody tr:nth-of-type(3) td:nth-of-type(3) input").should(
      "have.value",
      "g",
    );

    cy.findByText("a description of the synthesis here");
    cy.findByText("a comment is added here.");
    cy.findByText("a second comment is added here.");

    cy.findByText("Home").click();
  });

  it("uses the template id", () => {
    cy.contains("Add batch of samples").click();
    getBatchTemplateCell(1).type("test_{{}#{}}");

    // manually type names and a date
    getBatchAddCell(1, 2).type("testing 1");
    getBatchAddCell(2, 2).type("testing 1,2");
    getBatchAddCell(3, 2).type("testing 1,2,3");
    getBatchAddCell(1, 3).type("1992-12-10T14:34");

    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_3");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("test_1", "testing 1", "1992-12-10T14:34");
    verifySample("test_2", "testing 1,2");
    verifySample("test_3", "testing 1,2,3");

    deleteSample("test_1");
    deleteSample("test_2");
    deleteSample("test_3");
  });

  it("uses the template id, name, and date", () => {
    cy.contains("Add batch of samples").click();
    getBatchTemplateCell(1).type("test_{{}#{}}");
    getBatchTemplateCell(2).type("this is the test sample #{{}#{}}");
    getBatchTemplateCell(3).type("1980-02-01T05:35");

    cy.findByLabelText("start counting {#} at:").clear().type(5);

    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_5");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_6");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_7");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    verifySample("test_5", "this is the test sample #5", "1980-02-01T05:35");
    verifySample("test_6", "this is the test sample #6", "1980-02-01T05:35");
    verifySample("test_7", "this is the test sample #7", "1980-02-01T05:35");

    deleteSample("test_5");
    deleteSample("test_6");
    deleteSample("test_7");
  });

  it("uses the template id, name, date, copyFrom, and components", () => {
    cy.contains("Add batch of samples").click();
    getBatchTemplateCell(1).type("test_{{}#{}}");
    getBatchTemplateCell(2).type("this is the test sample #{{}#{}}");
    getBatchTemplateCell(3).type("1980-02-01T23:59");

    // select copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("baseA");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseA").click();
    });

    getBatchAddCell(1, 4).contains("baseA");
    getBatchAddCell(2, 4).contains("baseA");
    getBatchAddCell(3, 4).contains("baseA");

    // change the copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });

    getBatchAddCell(1, 4).contains("baseB");
    getBatchAddCell(2, 4).contains("baseB");
    getBatchAddCell(3, 4).contains("baseB");

    // add a component, check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component1").click();
    });
    getBatchAddCell(1, 5).contains("component1");
    getBatchAddCell(2, 5).contains("component1");
    getBatchAddCell(3, 5).contains("component1");

    // add another component, check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component2").click();
    });
    getBatchAddCell(1, 5).contains("component1");
    getBatchAddCell(1, 5).contains("component2");
    getBatchAddCell(2, 5).contains("component1");
    getBatchAddCell(2, 5).contains("component2");
    getBatchAddCell(3, 5).contains("component1");
    getBatchAddCell(3, 5).contains("component2");

    getSubmitButton().click();

    verifySample("test_1", "this is the test sample #1", "1980-02-01T00:00");
    verifySample("test_2", "this is the test sample #2", "1980-02-01T00:00");
    verifySample("test_3", "this is the test sample #3", "1980-02-01T00:00");

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_3");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();

    function checkCreatedSample(item_id) {
      cy.contains(item_id).click();
      cy.contains("this is a description of baseB.");
      cy.get("#synthesis-information table").contains("component3");
      cy.get("#synthesis-information table").contains("component4");
      cy.get("#synthesis-information table").contains("component1");
      cy.get("#synthesis-information table").contains("this component has a name");

      cy.get("#synthesis-information tbody tr:nth-of-type(1) input")
        .eq(0)
        .should("have.value", "30");
      cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
        .eq(0)
        .should("have.value", "100");
      cy.get("#synthesis-information tbody tr:nth-of-type(3) input").eq(0).should("have.value", "");

      cy.findByText("a comment is added here.");
      cy.findByText("a second comment is added here.");
      cy.findByText("Home").click();
    }

    checkCreatedSample("test_1");
    checkCreatedSample("test_2");
    checkCreatedSample("test_3");

    // deleteSample("test_1");
    // deleteSample("test_2");
    // deleteSample("test_3");;
  });

  it("plays with the number of rows", () => {
    cy.contains("Add batch of samples").click();
    cy.findByLabelText("Number of rows:").clear().type(3);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 3);

    cy.findByLabelText("Number of rows:").clear().type(0);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 0);

    getBatchTemplateCell(1).type("test{{}#{}}");
    getBatchTemplateCell(2).type("name{{}#{}}");

    getBatchTemplateCell(4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "baseB").click();
    });

    getBatchTemplateCell(5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component1").click();
    });

    getBatchTemplateCell(5, ".vs__search").type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component3").click();
    });

    getBatchTemplateCell(5, ".vs__search").type("component4");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "component4").click();
    });

    cy.findByLabelText("Number of rows:").clear().type(100);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 100);

    cy.findByLabelText("Number of rows:").clear().type(1);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 1);

    cy.findByLabelText("Number of rows:").clear().type(4);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 4);

    getBatchAddCell(1, 1, "input").should("have.value", "test1");
    getBatchAddCell(2, 1, "input").should("have.value", "test2");
    getBatchAddCell(3, 1, "input").should("have.value", "test3");
    getBatchAddCell(4, 1, "input").should("have.value", "test4");

    getBatchAddCell(1, 2, "input").should("have.value", "name1");
    getBatchAddCell(2, 2, "input").should("have.value", "name2");
    getBatchAddCell(3, 2, "input").should("have.value", "name3");
    getBatchAddCell(4, 2, "input").should("have.value", "name4");

    getBatchAddCell(1, 4).contains("baseB");
    getBatchAddCell(2, 4).contains("baseB");
    getBatchAddCell(3, 4).contains("baseB");
    getBatchAddCell(4, 4).contains("baseB");

    getBatchAddCell(1, 5).contains("component1");
    getBatchAddCell(2, 5).contains("component1");
    getBatchAddCell(3, 5).contains("component1");
    getBatchAddCell(4, 5).contains("component1");

    getBatchAddCell(1, 5).contains("component3");
    getBatchAddCell(2, 5).contains("component3");
    getBatchAddCell(3, 5).contains("component3");
    getBatchAddCell(4, 5).contains("component3");

    getBatchAddCell(1, 5).contains("component4");
    getBatchAddCell(2, 5).contains("component4");
    getBatchAddCell(3, 5).contains("component4");
    getBatchAddCell(4, 5).contains("component4");

    cy.findByLabelText("Number of rows:").clear().type(10);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 10);

    cy.findByLabelText("Number of rows:").type("{backspace}");
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 1);
    getBatchAddCell(1, 1, "input").should("have.value", "test1");
    getBatchAddCell(1, 2, "input").should("have.value", "name1");

    cy.findByLabelText("Number of rows:").clear().type(2);

    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test2");
    cy.findAllByText("Successfully created.").should("have.length", 2);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();

    function checkCreatedSample(item_id) {
      cy.contains(item_id).click();
      cy.contains("this is a description of baseB.");
      cy.get("#synthesis-information table").contains("component3");
      cy.get("#synthesis-information table").contains("component4");
      cy.get("#synthesis-information table").contains("component1");
      cy.get("#synthesis-information table").contains("this component has a name");

      cy.get("#synthesis-information tbody tr:nth-of-type(1) input")
        .eq(0)
        .should("have.value", "30");
      cy.get("#synthesis-information tbody tr:nth-of-type(2) input")
        .eq(0)
        .should("have.value", "100");
      cy.get("#synthesis-information tbody tr:nth-of-type(3) input").eq(0).should("have.value", "");

      cy.findByText("a comment is added here.");
      cy.findByText("a second comment is added here.");
      cy.findByText("Home").click();
    }

    verifySample("test1", "name1");
    verifySample("test2", "name2");
    checkCreatedSample("test1");
    checkCreatedSample("test2");
    deleteSample("test1");
    deleteSample("test2");
  });

  it("checks errors on the row", () => {
    cy.contains("Add batch of samples").click();
    cy.wait(100);
    getBatchTemplateCell("1").type("test10{{}#{}}");
    cy.findByLabelText("Number of rows:").clear().type(3);
    cy.wait(100);
    getSubmitButton().should("be.disabled");
    getBatchAddError(1).should("have.text", "test101 already in use.");
    getBatchAddError(2).should("have.text", "test102 already in use.");
    getBatchAddError(3).should("have.text", "test103 already in use.");

    cy.findByLabelText("Number of rows:").clear().type(4);
    getSubmitButton().should("be.disabled");
    getBatchAddError(4).should("have.text", "test104 already in use.");

    getBatchAddCell(1, 1).type("_unique");
    getBatchTemplateCell(1, "input").should("have.value", ""); // test_id template should be cleared by modifying an item_id
    getBatchAddError(1).invoke("text").invoke("trim").should("equal", ""); // expect no error for this row
    getSubmitButton().should("be.disabled"); // but submit is still disabled because there are still errors

    getBatchAddCell(3, 1).type("_unique");
    getBatchAddError(1).invoke("text").invoke("trim").should("equal", ""); // expect no error
    getBatchAddError(3).invoke("text").invoke("trim").should("equal", ""); // expect no error

    getBatchAddCell(2, 1).type("_unique");
    getBatchAddError(1).invoke("text").invoke("trim").should("equal", ""); // expect no error
    getBatchAddError(2).invoke("text").invoke("trim").should("equal", ""); // expect no error
    getBatchAddError(3).invoke("text").invoke("trim").should("equal", ""); // expect no error

    getBatchAddCell(2, 3).type("2000-01-01T10:05");

    getBatchAddCell(4, 1).clear();
    getBatchAddError(4).invoke("text").invoke("trim").should("not.equal", ""); // expect some error

    getBatchAddCell(4, 1).type("test101_unique");
    getBatchAddError(4).invoke("text").invoke("trim").should("not.equal", ""); // expect some error

    getSubmitButton().should("be.disabled");

    getBatchAddCell(4, 1).type("2");
    getBatchAddError(4).invoke("text").invoke("trim").should("equal", ""); // expect no error

    getSubmitButton().should("not.be.disabled"); // now all errors are fixed so submit is enabled
    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test101_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test102_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test103_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test101_unique2");
    cy.findAllByText("Successfully created.").should("have.length", 4);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();

    verifySample("test101_unique");
    verifySample("test102_unique", "", "2000-01-01T10:05");
    verifySample("test103_unique");
    verifySample("test101_unique2");
  });

  // as contains matches greedily, if any IDs have matching substrings they must be added in the appropriate order
  it("deletes the rest of the samples (cleanup)", () => {
    [
      "test102_unique",
      "test103_unique",
      "test101_unique2",
      "test101_unique",
      "component1",
      "component2",
      "component3",
      "component4",
      "baseA_copy",
      "baseB_copy2",
      "baseB_copy",
      "test101",
      "test102",
      "test103",
      "test104",
      "test_1",
      "test_2",
      "test_3",
      "baseA",
      "baseB",
    ].forEach((item_id) => {
      deleteSample(item_id);
    });
    cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
  });
});
