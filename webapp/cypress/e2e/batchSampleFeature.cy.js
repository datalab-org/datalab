const API_URL = Cypress.config("apiUrl");
console.log(API_URL);

// Any sample ID touched by these tests should be listed here for clean-up
let item_ids = [
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
  cy.cleanTestEnvironment({
    sampleIds: item_ids,
    visitPath: "/",
  });
});

after(() => {
  cy.cleanTestEnvironment({
    sampleIds: item_ids,
    visitPath: "/",
  });
});

describe("Batch sample creation", () => {
  beforeEach(() => {
    cy.visit("/");
  });
  it("Adds 3 valid samples", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddCell(1, 1).type("testA");
    cy.getBatchAddCell(2, 1).type("testB");
    cy.getBatchAddCell(2, 2).type("this sample has a name");
    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddCell(3, 1).type("testC");
    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "testA");
    cy.get("[data-testid=batch-modal-container]").contains("a", "testB");
    cy.get("[data-testid=batch-modal-container]").contains("a", "testC");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();
    cy.verifySample("testA");
    cy.verifySample("testB", "this sample has a name");
    cy.verifySample("testC");

    cy.deleteItems("sample", ["testA", "testB", "testC"]);
  });

  it("adds two valid samples", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.findByLabelText("Number of rows:").clear().type(2);

    cy.get('[data-testid="batch-modal-container"]').findByText("Submit").should("be.disabled");
    cy.getBatchAddCell(1, 1).type("baseA");
    cy.getBatchAddCell(2, 1).type("baseB");
    cy.getBatchAddCell(2, 2).type("the name of baseB");
    cy.getBatchAddCell(2, 3).type("1999-12-31T01:00");
    cy.getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB");
    cy.findAllByText("Successfully created.").should("have.length", 2);

    cy.closeAndWaitForModalToDisappear();
    cy.verifySample("baseA");
    cy.verifySample("baseB", "the name of baseB", "1999-12-31T01:00");
  });

  it("adds four base samples", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.findByLabelText("Number of rows:").clear().type(4);

    cy.get('[data-testid="batch-modal-container"]').findByText("Submit").should("be.disabled");
    cy.getBatchAddCell(1, 1).type("component1");
    cy.getBatchAddCell(1, 2).type("this component has a name");
    cy.getBatchAddCell(2, 1).type("component2");
    cy.getBatchAddCell(3, 1).type("component3");
    cy.getBatchAddCell(4, 1).type("component4");

    cy.getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "component1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component3");
    cy.get("[data-testid=batch-modal-container]").contains("a", "component4");

    cy.findAllByText("Successfully created.").should("have.length", 4);

    cy.closeAndWaitForModalToDisappear();
    cy.verifySample("component1", "this component has a name");
    cy.verifySample("component2");
    cy.verifySample("component3");
    cy.verifySample("component4");
  });

  it("modifies some data in the first sample", () => {
    cy.get('[data-testid="search-input"]').type("baseA");
    cy.findByText("baseA").click();
    cy.expandIfCollapsed("[data-testid=synthesis-block]");
    cy.findByLabelText("Description").type("this is a description of baseA.");
    cy.findByText("Add a block").click();
    cy.findByText("Comment").click();

    cy.get(".datablock-content div").first().type("a comment is added here.");

    cy.get(".fa-save").click();
    cy.findByText("Home").click();
  });

  it("modifies some data in the second sample", () => {
    cy.get('[data-testid="search-input"]').type("baseB");
    cy.findByText("baseB").click();
    cy.expandIfCollapsed("[data-testid=synthesis-block]");
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
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getBatchAddCell(1, 1).type("baseA_copy");
    cy.getBatchAddCell(1, 2).type("a copied sample");
    cy.selectVsOption(null, "baseA", { cellRow: 1, cellColumn: 4 });

    cy.getBatchAddCell(2, 1).type("baseB_copy");
    cy.selectVsOption(null, "baseB", { cellRow: 2, cellColumn: 4 });

    cy.getBatchAddCell(3, 1).type("baseB_copy2");
    cy.selectVsOption(null, "baseB", { cellRow: 3, cellColumn: 4 });

    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "baseA_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy");
    cy.get("[data-testid=batch-modal-container]").contains("a", "baseB_copy2");

    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();
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
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.findByLabelText("Number of rows:").clear().type(4);

    // sample with two components
    cy.getBatchAddCell(1, 1).type("test101");
    cy.getBatchAddCell(1, 2).type("sample with two components");
    cy.selectVsOption(null, "component1", { cellRow: 1, cellColumn: 5 });

    cy.selectVsOption(null, "component2", { cellRow: 1, cellColumn: 5 });

    // sample with two components, copied from a sample with no components
    cy.getBatchAddCell(2, 1).type("test102");
    cy.getBatchAddCell(2, 2).type(
      "sample with two components, copied from a sample with no components",
    );
    cy.selectVsOption(null, "baseA", { cellRow: 2, cellColumn: 4 });

    cy.selectVsOption(null, "component1", { cellRow: 2, cellColumn: 5 });

    cy.selectVsOption(null, "component2", { cellRow: 2, cellColumn: 5 });

    // sample with one components, copied from a sample with two components
    cy.getBatchAddCell(3, 1).type("test103");
    cy.getBatchAddCell(3, 2).type(
      "sample with one component, copied from a sample with two components",
    );
    cy.selectVsOption(null, "baseB", { cellRow: 3, cellColumn: 4 });

    cy.selectVsOption(null, "component1", { cellRow: 3, cellColumn: 5 });

    // sample with three components, copied from a sample with some of the same components
    cy.getBatchAddCell(4, 1).type("test104");
    cy.getBatchAddCell(4, 2).type(
      "sample with three components, copied from a sample with some of the same components",
    );
    cy.selectVsOption(null, "baseB", { cellRow: 4, cellColumn: 4 });

    cy.selectVsOption(null, "component2", { cellRow: 4, cellColumn: 5 });

    cy.selectVsOption(null, "component3", { cellRow: 4, cellColumn: 5 });

    cy.selectVsOption(null, "component4", { cellRow: 4, cellColumn: 5 });

    cy.getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "test101");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test102");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test103");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test104");

    cy.findAllByText("Successfully created.").should("have.length", 4);
    cy.closeAndWaitForModalToDisappear();
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
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getBatchTemplateCell(1).type("test_{{}#{}}");

    // manually type names and a date
    cy.getBatchAddCell(1, 2).type("testing 1");
    cy.getBatchAddCell(2, 2).type("testing 1,2");
    cy.getBatchAddCell(3, 2).type("testing 1,2,3");
    cy.getBatchAddCell(1, 3).type("1992-12-10T14:34");

    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_3");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();
    cy.verifySample("test_1", "testing 1", "1992-12-10T14:34");
    cy.verifySample("test_2", "testing 1,2");
    cy.verifySample("test_3", "testing 1,2,3");

    cy.deleteItems("sample", ["test_1", "test_2", "test_3"]);
  });

  it("uses the template id, name, and date", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getBatchTemplateCell(1).type("test_{{}#{}}");
    cy.getBatchTemplateCell(2).type("this is the test sample #{{}#{}}");
    cy.getBatchTemplateCell(3).type("1980-02-01T05:35");

    cy.findByLabelText("start counting {#} at:").clear().type(5);

    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_5");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_6");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_7");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();
    cy.verifySample("test_5", "this is the test sample #5", "1980-02-01T05:35");
    cy.verifySample("test_6", "this is the test sample #6", "1980-02-01T05:35");
    cy.verifySample("test_7", "this is the test sample #7", "1980-02-01T05:35");

    cy.deleteItems("sample", ["test_5", "test_6", "test_7"]);
  });

  it("uses the template id, name, date, copyFrom, and components", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getBatchTemplateCell(1).type("test_{{}#{}}");
    cy.getBatchTemplateCell(2).type("this is the test sample #{{}#{}}");
    cy.getBatchTemplateCell(3).type("1980-02-01T23:59");

    // select copyFrom sample, check that it is applied correctly
    cy.selectVsOption(null, "baseA", { cellColumn: 4 });

    cy.getBatchAddCell(1, 4).contains("baseA");
    cy.getBatchAddCell(2, 4).contains("baseA");
    cy.getBatchAddCell(3, 4).contains("baseA");

    // change the copyFrom sample, check that it is applied correctly
    cy.selectVsOption(null, "baseB", { cellColumn: 4 });

    cy.getBatchAddCell(1, 4).contains("baseB");
    cy.getBatchAddCell(2, 4).contains("baseB");
    cy.getBatchAddCell(3, 4).contains("baseB");

    // add a component, check that it is applied correctly
    cy.selectVsOption(null, "component1", { cellColumn: 5 });

    cy.getBatchAddCell(1, 5).contains("component1");
    cy.getBatchAddCell(2, 5).contains("component1");
    cy.getBatchAddCell(3, 5).contains("component1");

    // add another component, check that it is applied correctly
    cy.selectVsOption(null, "component2", { cellColumn: 5 });

    cy.getBatchAddCell(1, 5).contains("component1");
    cy.getBatchAddCell(1, 5).contains("component2");
    cy.getBatchAddCell(2, 5).contains("component1");
    cy.getBatchAddCell(2, 5).contains("component2");
    cy.getBatchAddCell(3, 5).contains("component1");
    cy.getBatchAddCell(3, 5).contains("component2");

    cy.getSubmitButton().click();

    cy.verifySample("test_1", "this is the test sample #1", "1980-02-01T00:00");
    cy.verifySample("test_2", "this is the test sample #2", "1980-02-01T00:00");
    cy.verifySample("test_3", "this is the test sample #3", "1980-02-01T00:00");

    cy.get("[data-testid=batch-modal-container]").contains("a", "test_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test_3");
    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();

    function checkCreatedSample(item_id) {
      cy.get('[data-testid="search-input"]').type(item_id);
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
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.findByLabelText("Number of rows:").clear().type(3);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 3);

    cy.findByLabelText("Number of rows:").clear().type(0);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 0);

    cy.getBatchTemplateCell(1).type("test{{}#{}}");
    cy.getBatchTemplateCell(2).type("name{{}#{}}");

    cy.selectVsOption(null, "baseB", { cellColumn: 4 });
    cy.selectVsOption(null, "component1", { cellColumn: 5 });
    cy.selectVsOption(null, "component3", { cellColumn: 5 });
    cy.selectVsOption(null, "component4", { cellColumn: 5 });

    cy.findByLabelText("Number of rows:").clear().type(100);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 100);

    cy.findByLabelText("Number of rows:").clear().type(1);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 1);

    cy.findByLabelText("Number of rows:").clear().type(4);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 4);

    cy.getBatchAddCell(1, 1, "input").should("have.value", "test1");
    cy.getBatchAddCell(2, 1, "input").should("have.value", "test2");
    cy.getBatchAddCell(3, 1, "input").should("have.value", "test3");
    cy.getBatchAddCell(4, 1, "input").should("have.value", "test4");

    cy.getBatchAddCell(1, 2, "input").should("have.value", "name1");
    cy.getBatchAddCell(2, 2, "input").should("have.value", "name2");
    cy.getBatchAddCell(3, 2, "input").should("have.value", "name3");
    cy.getBatchAddCell(4, 2, "input").should("have.value", "name4");

    cy.getBatchAddCell(1, 4).contains("baseB");
    cy.getBatchAddCell(2, 4).contains("baseB");
    cy.getBatchAddCell(3, 4).contains("baseB");
    cy.getBatchAddCell(4, 4).contains("baseB");

    cy.getBatchAddCell(1, 5).contains("component1");
    cy.getBatchAddCell(2, 5).contains("component1");
    cy.getBatchAddCell(3, 5).contains("component1");
    cy.getBatchAddCell(4, 5).contains("component1");

    cy.getBatchAddCell(1, 5).contains("component3");
    cy.getBatchAddCell(2, 5).contains("component3");
    cy.getBatchAddCell(3, 5).contains("component3");
    cy.getBatchAddCell(4, 5).contains("component3");

    cy.getBatchAddCell(1, 5).contains("component4");
    cy.getBatchAddCell(2, 5).contains("component4");
    cy.getBatchAddCell(3, 5).contains("component4");
    cy.getBatchAddCell(4, 5).contains("component4");

    cy.findByLabelText("Number of rows:").clear().type(10);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 10);

    cy.findByLabelText("Number of rows:").type("{backspace}");
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 1);
    cy.getBatchAddCell(1, 1, "input").should("have.value", "test1");
    cy.getBatchAddCell(1, 2, "input").should("have.value", "name1");

    cy.findByLabelText("Number of rows:").clear().type(2);

    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test2");
    cy.findAllByText("Successfully created.").should("have.length", 2);

    cy.closeAndWaitForModalToDisappear();

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
    cy.deleteItems("sample", ["test1", "test2"]);
  });

  it("checks errors on the row", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.getBatchTemplateCell("1").type("test10{{}#{}}");
    cy.wait(100);
    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddError(1).should("have.text", "test101 already in use.");
    cy.getBatchAddError(2).should("have.text", "test102 already in use.");
    cy.getBatchAddError(3).should("have.text", "test103 already in use.");

    cy.findByLabelText("Number of rows:").clear().type(4);
    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddError(4).should("have.text", "test104 already in use.");

    cy.getBatchAddCell(1, 1).type("_unique");
    cy.getBatchTemplateCell(1, "input").should("have.value", ""); // test_id template should be cleared by modifying an item_id
    cy.getBatchAddError(1).should("have.text", ""); // expect no error for this row
    cy.getSubmitButton().should("be.disabled"); // but submit is still disabled because there are still errors

    cy.getBatchAddCell(2, 1).type("_unique");
    cy.getBatchAddError(1).should("have.text", ""); // expect no error for this row
    cy.getBatchAddError(2).should("have.text", ""); // expect no error for this row

    cy.getBatchAddCell(3, 1).type("_unique");
    cy.getBatchAddError(1).should("have.text", ""); // expect no error for this row
    cy.getBatchAddError(2).should("have.text", ""); // expect no error for this row
    cy.getBatchAddError(3).should("have.text", ""); // expect no error for this row

    cy.getBatchAddCell(2, 3).type("2000-01-01T10:05");

    cy.getBatchAddCell(4, 1).clear();
    cy.getBatchAddError(4).invoke("text").invoke("trim").should("not.equal", ""); // expect some error

    cy.getBatchAddCell(4, 1).type("test101_unique");
    cy.getBatchAddError(4).invoke("text").invoke("trim").should("not.equal", ""); // expect some error

    cy.getSubmitButton().should("be.disabled");

    cy.getBatchAddCell(4, 1).type("2");
    cy.getBatchAddError(4).should("have.text", ""); // expect no error for this row

    cy.getSubmitButton().should("not.be.disabled"); // now all errors are fixed so submit is enabled
    cy.getSubmitButton().click();

    cy.get("[data-testid=batch-modal-container]").contains("a", "test101_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test102_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test103_unique");
    cy.get("[data-testid=batch-modal-container]").contains("a", "test101_unique2");
    cy.findAllByText("Successfully created.").should("have.length", 4);

    cy.closeAndWaitForModalToDisappear();

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
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.get("[data-testid=batch-modal-container]").findByLabelText("Type:").select("cell");
    cy.findByLabelText("Number of rows:").clear().type(4);
    cy.get("[data-testid=batch-add-table] > tbody > tr").should("have.length", 4);

    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddCell(1, 1, "input").type("cell_A");
    // set positive electrode for the first cell
    cy.selectVsOption(null, "abcdef", { cellRow: 1, cellColumn: 5, index: 0, withBadge: false });

    cy.getBatchAddCell(2, 1, "input").type("cell_B");
    cy.getBatchAddCell(2, 2, "input").type("this cell has a name");

    cy.getSubmitButton().should("be.disabled");
    cy.getBatchAddCell(3, 1, "input").type("cell_C");
    cy.getBatchAddCell(3, 3, "input").type("2017-06-01T08:30");
    cy.getBatchAddCell(4, 1, "input").type("cell_D");

    cy.getSubmitButton().click();

    cy.verifySample("cell_A");
    cy.verifySample("cell_B", "this cell has a name");
    cy.verifySample("cell_C", null, "2017-06-01");
    cy.verifySample("cell_D");
  });

  it("adds some component samples to be used for the next tests", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");
    cy.findByLabelText("Number of rows:").clear().type(2);

    cy.getBatchAddCell(1, 1).type("comp1");
    cy.getBatchAddCell(1, 2).type("comp1 name");
    cy.getBatchAddCell(2, 1).type("comp2");

    cy.getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "comp1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "comp2");
  });

  it("creates a batch of cells using the template id, name, date, copyFrom, and components", () => {
    cy.openAndWaitForModal("[data-testid=batch-item-button]");

    cy.get("[data-testid=batch-modal-container]").findByLabelText("Type:").select("cell");

    cy.getBatchTemplateCell(1, "input").eq(0).type("cell_{{}#{}}");
    cy.getBatchTemplateCell(2, "input").type("this is the test cell #{{}#{}}");
    cy.getBatchTemplateCell(3, "input").type("1980-02-01T23:59");

    // select copyFrom sample, check that it is applied correctly
    cy.selectVsOption(null, "cell_B", { cellColumn: 4 });

    cy.getBatchAddCell(1, 4).contains("cell_B");
    cy.getBatchAddCell(2, 4).contains("cell_B");
    cy.getBatchAddCell(3, 4).contains("cell_B");

    // change the copyFrom sample, check that it is applied correctly
    cy.selectVsOption(null, "cell_A", { cellColumn: 4 });

    cy.getBatchAddCell(1, 4).contains("cell_A");
    cy.getBatchAddCell(2, 4).contains("cell_A");
    cy.getBatchAddCell(3, 4).contains("cell_A");

    // add a positive electrode, check that it is applied correctly
    cy.selectVsOption(null, "comp1", { cellColumn: 5, index: 0, withBadge: true });

    cy.getBatchAddCell(1, 5).contains("comp1");
    cy.getBatchAddCell(2, 5).contains("comp1");
    cy.getBatchAddCell(3, 5).contains("comp1");

    // add another component, this one tagged (i.e., not in the db) check that it is applied correctly
    cy.selectVsOption(null, "tagged", { cellColumn: 5, index: 0, withBadge: false });

    cy.getBatchAddCell(1, 5).contains("comp1");
    cy.getBatchAddCell(1, 5).contains("tagged");
    cy.getBatchAddCell(2, 5).contains("comp1");
    cy.getBatchAddCell(2, 5).contains("tagged");
    cy.getBatchAddCell(3, 5).contains("comp1");
    cy.getBatchAddCell(3, 5).contains("tagged");

    // add electrolyte
    cy.selectVsOption(null, "elyte", { cellColumn: 5, index: 1, withBadge: false });

    cy.getBatchAddCell(1, 5).contains("elyte");
    cy.getBatchAddCell(2, 5).contains("elyte");
    cy.getBatchAddCell(3, 5).contains("elyte");

    // add negative electrode
    cy.selectVsOption(null, "comp2", { cellColumn: 5, index: 2, withBadge: true });

    cy.getBatchAddCell(1, 5).contains("comp2");
    cy.getBatchAddCell(2, 5).contains("comp2");
    cy.getBatchAddCell(3, 5).contains("comp2");

    cy.getSubmitButton().click();
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_1");
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_2");
    cy.get("[data-testid=batch-modal-container]").contains("a", "cell_3");

    cy.findAllByText("Successfully created.").should("have.length", 3);

    cy.closeAndWaitForModalToDisappear();

    cy.verifySample("cell_1", "this is the test cell #1", "1980-02-01T23:59");
    cy.verifySample("cell_2", "this is the test cell #2", "1980-02-01T23:59");
    cy.verifySample("cell_3", "this is the test cell #3", "1980-02-01T23:59");

    function checkCreatedCell(item_id) {
      cy.get('[data-testid="search-input"]').type(item_id);
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
