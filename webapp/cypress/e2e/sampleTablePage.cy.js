const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

const TODAY = new Date().toISOString().slice(0, -8);

function createSample(sample_id, name = null, date = null) {
  cy.findByText("Add an item").click();
  cy.findByText("Add new sample").should("exist");
  cy.findByLabelText("Sample ID:").type(sample_id);
  if (name) {
    cy.findByLabelText("Sample Name:").type(name);
  }
  if (date) {
    cy.findByLabelText("Date Created:").type(date);
  }
  cy.contains("Submit").click();
}

function verifySample(sample_id, name = null, date = null) {
  if (date) {
    cy.findByText(sample_id)
      .parents("tr")
      .within(() => {
        cy.findByText(date.split("T")[0]);
        if (name) {
          cy.findByText(name);
        }
      });
  } else {
    cy.findByText(sample_id)
      .parents("tr")
      .within(() => {
        cy.findByText(TODAY.split("T")[0]);
        if (name) {
          cy.findByText(name);
        }
      });
  }
}

function deleteSample(sample_id) {
  // wait a bit to allow things to settle
  cy.wait(100).then(() => {
    cy.findByText(sample_id)
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
    cy.findByLabelText("Sample ID:").type("12345678910");
    cy.findByLabelText("Date Created:").type("1990-01-07T00:00");

    cy.findByLabelText("Sample Name:").type("This is a sample name");
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
    cy.findByLabelText("Sample ID").should("have.value", "12345678910");
    cy.go("back");
    cy.findByText("12345678910");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
  });

  it("Attempts to Add an item with the same name", () => {
    cy.findByText("Add an item").click();
    cy.findByText("Add new sample").should("exist");
    cy.findByLabelText("Sample ID:").type("12345678910");

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
      }
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
    cy.findByLabelText("Sample ID").should("have.value", "122.rwre");
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
      }
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
    cy.findByLabelText("Sample ID:").type("testAcopy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testA");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("testA").click();
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
    cy.get("#synthesis-information .vs__search").first().type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("component3").click();
    });
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").eq(0).type("30");

    cy.get("#synthesis-information .vs__search").first().type("component4");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("component4").click();
    });
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).type("100"); // eq(1) gets the second element that matches

    cy.findByLabelText("Procedure").type("a description of the synthesis here");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();

    /* ==== End Cypress Studio ==== */
  });

  it("copies the second sample", () => {
    cy.findByText("Add an item").click();
    cy.findByLabelText("Sample ID:").type("testBcopy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testB");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("testB").click();
    });
    cy.contains("Submit").click();
    verifySample("testBcopy", "COPY OF the second test sample");
  });

  it("checks the edit page of the copied sample", () => {
    cy.findByText("testBcopy").click();
    cy.findByLabelText("Sample ID").should("have.value", "testBcopy");
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
    cy.findByLabelText("Sample ID:").type("testBcopy_copy");
    cy.findByLabelText("(Optional) Copy from existing sample:").type("testBcopy");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("testBcopy").click();
    });

    cy.findByLabelText("(Optional) Start with constituents:").type("component2");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("component2").click();
    });
    cy.findByLabelText("(Optional) Start with constituents:").type("component3");
    cy.get(".vs__dropdown-menu").within(() => {
      cy.findByText("component3").click();
    });

    cy.contains("Submit").click();
    verifySample("testBcopy_copy", "COPY OF COPY OF the second test sample");
  });

  it("checks the edit page of the copied sample with components", () => {
    cy.findByText("testBcopy_copy").click();
    cy.findByLabelText("Sample ID").should("have.value", "testBcopy_copy");
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
      "testB",
      "testAcopy",
      "component1",
      "component2",
      "component3",
      "component4",
      "testBcopy",
      "testBcopy_copy",
    ].map((id) => {
      deleteSample(id);
    });
  });
});
