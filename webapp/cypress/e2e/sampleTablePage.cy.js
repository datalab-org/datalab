const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

let sample_ids = [];

before(() => {
  cy.visit("/");
  cy.removeAllTestSamples(sample_ids);
});

after(() => {
  cy.visit("/");
  cy.removeAllTestSamples(sample_ids);
});

describe("Sample table page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

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

    cy.request({ url: `${API_URL}/get-item-data/12345678910`, failOnStatusCode: false }).then(
      (resp) => {
        expect(resp.status).to.be.gte(400).lt(500);
      },
    );
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

describe("Advanced sample creation features", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds some valid samples", () => {
    cy.createSample("testA", "the first test sample");
    cy.createSample("testB", "the second test sample");
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
  });

  it("copies the second sample", () => {
    cy.findByText("Add an item").click();
    cy.findByLabelText("ID:").type("testBcopy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.contains(".badge", "testB").click();
    });
    cy.contains("Submit").click();
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
});
