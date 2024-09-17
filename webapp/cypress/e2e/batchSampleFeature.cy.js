const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

// eslint-disable-next-line no-unused-vars
let consoleSpy; // keeps track of every time an error is written to the console
Cypress.on("window:before:load", (win) => {
  consoleSpy = cy.spy(win.console, "error");
});

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

// Any sample ID touched by these tests should be listed here for clean-up
let sample_ids = [
  "testA",
  "testB",
  "testC",
  "baseA",
  "baseB",
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
  "test_4",
  "test_5",
  "test_6",
  "test_7",
  "test102_unique",
  "test103_unique",
  "test101_unique2",
  "test101_unique",
  "cell_A",
  "cell_B",
  "cell_C",
  "cell_D",
  "comp1",
  "comp2",
  "cell_1",
  "cell_2",
  "cell_3",
];

before(() => {
  cy.visit("/");
  cy.removeAllTestSamples(sample_ids, true);
});

after(() => {
  cy.visit("/");
  cy.removeAllTestSamples(sample_ids, true);
});

describe("Batch sample creation", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds 3 valid samples", () => {
    cy.contains("Add batch of items").click();
    getSubmitButton().should("be.disabled");
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
    cy.verifySample("testA");
    cy.verifySample("testB", "this sample has a name");
    cy.verifySample("testC");

    cy.deleteSample("testA");
    cy.deleteSample("testB");
    cy.deleteSample("testC");
  });

  it("adds two valid samples", () => {
    cy.contains("Add batch of items").click();
    cy.findByLabelText("Number of rows:").clear().type(2);

    cy.get('[data-testid="batch-modal-container"]').findByText("Submit").should("be.disabled");
    getBatchAddCell(1, 1).type("baseA");
    getBatchAddCell(2, 1).type("baseB");
    getBatchAddCell(2, 2).type("the name of baseB");
    getBatchAddCell(2, 3).type("1999-12-31T01:00");
    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB");
    cy.findAllByText("Successfully created.").should("have.length", 2);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    cy.verifySample("baseA");
    cy.verifySample("baseB", "the name of baseB", "1999-12-31T01:00");
  });

  it("adds four base samples", () => {
    cy.contains("Add batch of items").click();
    cy.findByLabelText("Number of rows:").clear().type(4);

    cy.get('[data-testid="batch-modal-container"]').findByText("Submit").should("be.disabled");
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
    cy.verifySample("component1", "this component has a name");
    cy.verifySample("component2");
    cy.verifySample("component3");
    cy.verifySample("component4");
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

    cy.searchAndSelectItem("component3", "#synthesis-information .vs__search");
    cy.get("#synthesis-information tbody tr:nth-of-type(1) input").first().type("30");

    cy.searchAndSelectItem("component4", "#synthesis-information .vs__search", true);
    cy.get("#synthesis-information tbody tr:nth-of-type(2) input").eq(0).type("100");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();
  });

  it("makes samples copied from others", () => {
    cy.contains("Add batch of items").click();
    getBatchAddCell(1, 1).type("baseA_copy");
    getBatchAddCell(1, 2).type("a copied sample");
    getBatchAddCell(1, 4, ".vs__search").type("BaseA");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseA").click();

    getBatchAddCell(2, 1).type("baseB_copy");
    getBatchAddCell(2, 4, ".vs__search").type("BaseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getBatchAddCell(3, 1).type("baseB_copy2");
    getBatchAddCell(3, 4, ".vs__search").type("BaseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy2");

    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();
    cy.verifySample("baseA_copy", "a copied sample");
    cy.verifySample("baseB_copy");
    cy.verifySample("baseB_copy2");
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
    cy.contains("Add batch of items").click();
    cy.findByLabelText("Number of rows:").clear().type(4);

    // sample with two components
    getBatchAddCell(1, 1).type("test101");
    getBatchAddCell(1, 2).type("sample with two components");
    getBatchAddCell(1, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();

    getBatchAddCell(1, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();

    // sample with two components, copied from a sample with no components
    getBatchAddCell(2, 1).type("test102");
    getBatchAddCell(2, 2).type(
      "sample with two components, copied from a sample with no components",
    );
    getBatchAddCell(2, 4, ".vs__search").type("baseA");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseA").click();

    getBatchAddCell(2, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();

    getBatchAddCell(2, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();

    // sample with one components, copied from a sample with two components
    getBatchAddCell(3, 1).type("test103");
    getBatchAddCell(3, 2).type(
      "sample with one component, copied from a sample with two components",
    );
    getBatchAddCell(3, 4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getBatchAddCell(3, 5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();

    // sample with three components, copied from a sample with some of the same components
    getBatchAddCell(4, 1).type("test104");
    getBatchAddCell(4, 2).type(
      "sample with three components, copied from a sample with some of the same components",
    );
    getBatchAddCell(4, 4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getBatchAddCell(4, 5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();

    getBatchAddCell(4, 5, ".vs__search").type("component3");
    cy.get(".vs__dropdown-menu").contains(".badge", "component3").click();

    getBatchAddCell(4, 5, ".vs__search").type("component4");
    cy.get(".vs__dropdown-menu").contains(".badge", "component4").click();

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
    cy.contains("Add batch of items").click();
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
    cy.verifySample("test_1", "testing 1", "1992-12-10T14:34");
    cy.verifySample("test_2", "testing 1,2");
    cy.verifySample("test_3", "testing 1,2,3");

    cy.deleteSample("test_1");
    cy.deleteSample("test_2");
    cy.deleteSample("test_3");
  });

  it("uses the template id, name, and date", () => {
    cy.contains("Add batch of items").click();
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
    cy.verifySample("test_5", "this is the test sample #5", "1980-02-01T05:35");
    cy.verifySample("test_6", "this is the test sample #6", "1980-02-01T05:35");
    cy.verifySample("test_7", "this is the test sample #7", "1980-02-01T05:35");

    cy.deleteSample("test_5");
    cy.deleteSample("test_6");
    cy.deleteSample("test_7");
  });

  it("uses the template id, name, date, copyFrom, and components", () => {
    cy.contains("Add batch of items").click();
    getBatchTemplateCell(1).type("test_{{}#{}}");
    getBatchTemplateCell(2).type("this is the test sample #{{}#{}}");
    getBatchTemplateCell(3).type("1980-02-01T23:59");

    // select copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("baseA");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseA").click();

    getBatchAddCell(1, 4).contains("baseA");
    getBatchAddCell(2, 4).contains("baseA");
    getBatchAddCell(3, 4).contains("baseA");

    // change the copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getBatchAddCell(1, 4).contains("baseB");
    getBatchAddCell(2, 4).contains("baseB");
    getBatchAddCell(3, 4).contains("baseB");

    // add a component, check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();

    getBatchAddCell(1, 5).contains("component1");
    getBatchAddCell(2, 5).contains("component1");
    getBatchAddCell(3, 5).contains("component1");

    // add another component, check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").type("component2");
    cy.get(".vs__dropdown-menu").contains(".badge", "component2").click();

    getBatchAddCell(1, 5).contains("component1");
    getBatchAddCell(1, 5).contains("component2");
    getBatchAddCell(2, 5).contains("component1");
    getBatchAddCell(2, 5).contains("component2");
    getBatchAddCell(3, 5).contains("component1");
    getBatchAddCell(3, 5).contains("component2");

    getSubmitButton().click();

    cy.verifySample("test_1", "this is the test sample #1", "1980-02-01T00:00");
    cy.verifySample("test_2", "this is the test sample #2", "1980-02-01T00:00");
    cy.verifySample("test_3", "this is the test sample #3", "1980-02-01T00:00");

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
  });

  it("plays with the number of rows", () => {
    cy.contains("Add batch of items").click();
    cy.findByLabelText("Number of rows:").clear().type(3);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 3);

    cy.findByLabelText("Number of rows:").clear().type(0);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 0);

    getBatchTemplateCell(1).type("test{{}#{}}");
    getBatchTemplateCell(2).type("name{{}#{}}");

    getBatchTemplateCell(4, ".vs__search").type("baseB");
    cy.get(".vs__dropdown-menu").contains(".badge", "baseB").click();

    getBatchTemplateCell(5, ".vs__search").type("component1");
    cy.get(".vs__dropdown-menu").contains(".badge", "component1").click();

    getBatchTemplateCell(5, ".vs__search").type("component3");
    cy.get(".vs__dropdown-menu").contains(".badge", "component3").click();

    getBatchTemplateCell(5, ".vs__search").type("component4");
    cy.get(".vs__dropdown-menu").contains(".badge", "component4").click();

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

    cy.verifySample("test1", "name1");
    cy.verifySample("test2", "name2");
    checkCreatedSample("test1");
    checkCreatedSample("test2");
    cy.deleteSample("test1");
    cy.deleteSample("test2");
  });

  it("checks errors on the row", () => {
    cy.contains("Add batch of items").click();
    getBatchTemplateCell("1").type("test10{{}#{}}");
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

    cy.verifySample("test101_unique");
    cy.verifySample("test102_unique", "", "2000-01-01T10:05");
    cy.verifySample("test103_unique");
    cy.verifySample("test101_unique2");
  });
});

describe("Batch cell creation", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("creates a simple batch of cells", () => {
    cy.contains("Add batch of items").click();
    cy.get("[data-testid=batch-modal-container]").findByLabelText("Type:").select("cell");
    cy.findByLabelText("Number of rows:").clear().type(4);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 4);

    getSubmitButton().should("be.disabled");
    getBatchAddCell(1, 1, "input").type("cell_A");
    // set positive electrode for the first cell
    getBatchAddCell(1, 5, "input.vs__search").eq(0).type("abcdef");
    cy.get(".vs__dropdown-menu").contains("abcdef").click();

    getBatchAddCell(2, 1, "input").type("cell_B");
    getBatchAddCell(2, 2, "input").type("this cell has a name");

    getSubmitButton().should("be.disabled");
    getBatchAddCell(3, 1, "input").type("cell_C");
    getBatchAddCell(3, 3, "input").type("2017-06-01T08:30");
    getBatchAddCell(4, 1, "input").type("cell_D");

    getSubmitButton().click();

    cy.verifySample("cell_A");
    cy.verifySample("cell_B", "this cell has a name");
    cy.verifySample("cell_C", null, "2017-06-01");
    cy.verifySample("cell_D");
  });

  it("adds some component samples to be used for the next tests", () => {
    cy.contains("Add batch of items").click();
    cy.findByLabelText("Number of rows:").clear().type(2);

    getBatchAddCell(1, 1).type("comp1");
    getBatchAddCell(1, 2).type("comp1 name");
    getBatchAddCell(2, 1).type("comp2");

    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "comp1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "comp2");
  });

  it("creates a batch of cells using the template id, name, date, copyFrom, and components", () => {
    cy.contains("Add batch of items").click();

    cy.get("[data-testid=batch-modal-container]").findByLabelText("Type:").select("cell");

    getBatchTemplateCell(1, "input").eq(0).type("cell_{{}#{}}");
    getBatchTemplateCell(2, "input").type("this is the test cell #{{}#{}}");
    getBatchTemplateCell(3, "input").type("1980-02-01T23:59");

    // select copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("cell_B");
    cy.get(".vs__dropdown-menu").contains(".badge", "cell_B").click();

    getBatchAddCell(1, 4).contains("cell_B");
    getBatchAddCell(2, 4).contains("cell_B");
    getBatchAddCell(3, 4).contains("cell_B");

    // change the copyFrom sample, check that it is applied correctly
    getBatchTemplateCell(4, ".vs__search").type("cell_A");
    cy.get(".vs__dropdown-menu").contains(".badge", "cell_A").click();

    getBatchAddCell(1, 4).contains("cell_A");
    getBatchAddCell(2, 4).contains("cell_A");
    getBatchAddCell(3, 4).contains("cell_A");

    // add a positive electrode, check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").eq(0).type("comp1");
    cy.get(".vs__dropdown-menu").contains(".badge", "comp1").click();

    getBatchAddCell(1, 5).contains("comp1");
    getBatchAddCell(2, 5).contains("comp1");
    getBatchAddCell(3, 5).contains("comp1");

    // add another component, this one tagged (i.e., not in the db) check that it is applied correctly
    getBatchTemplateCell(5, ".vs__search").eq(0).type("tagged");
    cy.get(".vs__dropdown-menu").eq(0).contains("tagged").click();

    getBatchAddCell(1, 5).contains("comp1");
    getBatchAddCell(1, 5).contains("tagged");
    getBatchAddCell(2, 5).contains("comp1");
    getBatchAddCell(2, 5).contains("tagged");
    getBatchAddCell(3, 5).contains("comp1");
    getBatchAddCell(3, 5).contains("tagged");

    // add electrolyte
    getBatchTemplateCell(5, ".vs__search").eq(1).type("elyte");
    cy.get(".vs__dropdown-menu").eq(0).contains("elyte").click();
    getBatchAddCell(1, 5).contains("elyte");
    getBatchAddCell(2, 5).contains("elyte");
    getBatchAddCell(3, 5).contains("elyte");

    // add negative electrode
    getBatchTemplateCell(5, ".vs__search").eq(2).type("comp2");
    cy.get(".vs__dropdown-menu").eq(0).contains(".badge", "comp2").click();
    getBatchAddCell(1, 5).contains("comp2");
    getBatchAddCell(2, 5).contains("comp2");
    getBatchAddCell(3, 5).contains("comp2");

    getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_3");

    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.get("[data-testid=batch-modal-container]").contains("Close").click();

    cy.verifySample("cell_1", "this is the test cell #1", "1980-02-01T23:59");
    cy.verifySample("cell_2", "this is the test cell #2", "1980-02-01T23:59");
    cy.verifySample("cell_3", "this is the test cell #3", "1980-02-01T23:59");

    function checkCreatedCell(item_id) {
      cy.contains(item_id).click();
      cy.get("#pos-electrode-table").contains("comp1");
      cy.get("#pos-electrode-table").contains("tagged");
      cy.get("#pos-electrode-table").contains("comp1 name");

      cy.get("#electrolyte-table").contains("elyte");

      cy.get("#neg-electrode-table").contains("comp2");

      cy.findByText("Home").click();
    }

    checkCreatedCell("cell_1");
    checkCreatedCell("cell_2");
    checkCreatedCell("cell_3");
  });
});
