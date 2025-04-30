const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

let item_ids = ["editable_sample", "component1", "component2"];

before(() => {
  cy.visit("/");
  cy.removeAllTestSamples(item_ids, true);
});

after(() => {
  cy.visit("/");
  cy.removeAllTestSamples(item_ids, true);
});

describe("Edit Page", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("Loads the main page without any errors", () => {
    cy.findByText("About").should("exist");
    cy.findByText("Samples").should("exist");
    cy.findByText("Add an item").should("exist");

    cy.contains("Server Error. Sample list could not be retreived.").should("not.exist");
    expect(consoleSpy).not.to.be.called;
  });

  it("Adds a valid sample", () => {
    cy.createSample("editable_sample", "This is a sample name", "1990-01-07T00:00");
    cy.get("tr>td").eq(8).should("be.empty"); // 0 blocks are present
    cy.get("tr>td").eq(9).should("be.empty"); // 0 files are present
  });

  it("Add some more samples, to use as components", () => {
    cy.createSample("component1", "This is a component");
    cy.createSample("component2", "This is another component");
  });

  it("Checks editing the sample edit page", () => {
    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();
    cy.findByLabelText("Name").should("have.value", "This is a sample name");
    cy.findByLabelText("Chemical formula").type("NaCoO2", { force: true });

    cy.findByText("Unsaved changes");
    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");
    cy.findByText("Home").click();

    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample");
    cy.findByText("This is a sample name");
    cy.findByText("1990-01-07");
    cy.findByText("NaCoO2"); // sorta check the formula
  });

  it("adds a chemical formula to component1", () => {
    cy.findByText("component1").click();
    cy.findByLabelText("Chemical formula").type("Na2O", { force: true });

    cy.findByText("Unsaved changes");
    cy.wait(100).then(() => cy.get(".fa-save").click());
    cy.contains("Unsaved changes").should("not.exist");
  });

  it("adds some synthesis information", () => {
    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();
    cy.expandIfCollapsed("[data-testid=synthesis-block]");
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
    cy.get('[data-testid="search-input"]').type("editable_sample");
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
    cy.get('[data-testid="search-input"]').type("editable_sample");
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
    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();

    cy.findByText("Add a block").click();
    cy.get('[data-testid="add-block-dropdown"]').findByText("Comment").click();

    cy.contains("Unsaved changes").should("not.exist");

    cy.findByText("Add a block").click();
    cy.get('[data-testid="add-block-dropdown"]').findByText("Comment").click();

    cy.contains("Unsaved changes").should("not.exist");

    cy.get(".datablock-content div").eq(0).type("the first comment box");
    cy.contains("Unsaved changes");

    // click update block icon and make sure unsaved changes warning goes away
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(0).click();
    cy.contains("Unsaved changes").should("not.exist");
    cy.get(".datablock-content div").eq(0).contains("the first comment box");

    cy.get(".datablock-content div").eq(0).type("\nThe first comment box; further changes.");
    cy.contains("Unsaved changes");

    cy.get('[data-testid="block-description"]').eq(0).type("The second comment box");
    cy.contains("Unsaved changes");
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(1).click();
    cy.wait(500).then(() => {
      cy.contains("Unsaved changes"); // unsaved changes warning should still exist since first block is still edited
    });
    cy.get('.datablock-header [aria-label="updateBlock"]').eq(0).click();
    cy.contains("Unsaved changes").should("not.exist");

    cy.get('[data-testid="block-description"]')
      .eq(0)
      .type("\nThe second comment box; further changes");
    cy.findByLabelText("Name").type("name change");
    cy.contains("Unsaved changes");

    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");

    cy.findByText("Home").click();
    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.get("[data-testid=sample-table] tr:nth-of-type(1) > td:nth-of-type(9)").contains(2); // 2 blocks are present
  });

  it("Clicks the upload buttons and checks that the modals are shown", () => {
    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();

    cy.findByText("Upload files...").click();
    cy.get(".uppy-Dashboard-AddFiles-title").should("contain.text", "Drop files here,");
    cy.get(".uppy-Dashboard-AddFiles-title").should("contain.text", "browse files");
    cy.get(".uppy-Dashboard-AddFiles-title").should("contain.text", "or import from:");
    cy.findByLabelText("Close Modal").click();

    cy.findByText("Add files from server...").click();
    cy.findByText("Select files to add").should("exist");
  });

  it("Uploads an XRD file, makes an XRD block and checks that the plot works", () => {
    cy.uploadFileViaAPI("editable_sample", "example_data/XRD/example_bmb.xye");

    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();

    cy.findByText("Add a block").click();
    cy.get('[data-testid="add-block-dropdown"]').findByText("Powder XRD").click();

    cy.findByText("Select a file:").should("exist");
    cy.get("select.file-select-dropdown").select("example_data_XRD_example_bmb.xye");
    cy.contains("label", "X axis").should("exist");
    cy.contains("label", "Y axis").should("exist");
  });

  it("Uploads a fake PNG image, make a Media block and checks that the image is shown", () => {
    let test_fname = "test_image.png";
    cy.createTestPNG(test_fname);
    cy.uploadFileViaAPI("editable_sample", test_fname);

    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();

    cy.findByText("Add a block").click();
    cy.get('[data-testid="add-block-dropdown"]').findByText("Media").click();
    cy.findAllByText("Select a file:").eq(1).should("exist");
    cy.get("select.file-select-dropdown").eq(1).select(test_fname);

    // Check that the img with id "media-block-img" is present
    cy.get('img[data-testid="media-block-img"]').should("exist");
  });

  it("Uploads an Raman data file, makes a Raman block and checks that the plot is shown", () => {
    cy.uploadFileViaAPI("editable_sample", "example_data/raman/labspec_raman_example.txt");

    cy.get('[data-testid="search-input"]').type("editable_sample");
    cy.findByText("editable_sample").click();

    cy.findByText("Add a block").click();
    cy.get('[data-testid="add-block-dropdown"]').findByText("Raman spectroscopy").click();
    cy.findAllByText("Select a file:").eq(2).should("exist");
    cy.get("select.file-select-dropdown")
      .eq(2)
      .select("example_data_raman_labspec_raman_example.txt");
    cy.contains("label", "X axis").should("exist");
    cy.contains("label", "Y axis").should("exist");
  });
});
