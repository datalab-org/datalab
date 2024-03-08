// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

import "@testing-library/cypress/add-commands";

// Alternatively you can use CommonJS syntax:
// require('./commands')
const TODAY = new Date().toISOString().slice(0, -8);
const API_URL = Cypress.config("apiUrl");

Cypress.Commands.add("createSample", (sample_id, name = null, date = null) => {
  cy.findByText("Add an item").click();
  cy.findByText("Add new sample").should("exist");
  cy.findByLabelText("ID:").type(sample_id);
  if (name) {
    cy.get("#sample-name").type(name);
  }
  if (date) {
    cy.findByLabelText("Date Created:").type(date);
  }
  cy.get("#sample-submit").click();
});

Cypress.Commands.add("verifySample", (sample_id, name = null, date = null) => {
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
});

Cypress.Commands.add("deleteSample", (sample_id, delay = 100) => {
  cy.visit("/");
  cy.wait(delay).then(() => {
    cy.log("search for and delete: " + sample_id);
    cy.get("[data-testid=sample-table]")
      .contains(new RegExp("^" + sample_id + "$", "g"))
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });
  });
});

Cypress.Commands.add("deleteSampleViaAPI", (sample_id) => {
  cy.log("search for and delete: " + sample_id);
  cy.request({
    method: "POST",
    url: API_URL + "/delete-sample/",
    body: { item_id: sample_id },
    failOnStatusCode: false,
  });
});

Cypress.Commands.add(
  "searchAndSelectItem",
  (search_text, selector, clickPlus = false, delay = 100) => {
    // searches in the dropdown for the first real item with the given name, looking for a badge
    // if clickPlus, then also click the add row button before looking for the search bar
    if (clickPlus) {
      cy.get("#synthesis-information").within(() => {
        cy.get("svg.add-row-button").click();
      });
    }
    cy.get(selector).first().type(search_text);
    cy.wait(delay).then(() => {
      cy.get(".vs__dropdown-menu").within(() => {
        cy.contains(".badge", search_text).click();
      });
    });
  },
);

Cypress.Commands.add("removeAllTestSamples", (sample_ids) => {
  // as contains matches greedily, if any IDs have matching substrings they must be added in the appropriate order
  sample_ids = [
    "editable_sample",
    "component1",
    "component2",
    "testAcopy",
    "component1",
    "component2",
    "component3",
    "component4",
    "testBcopy_copy",
    "testBcopy",
    "testB",
    "testA",
    "sdlkfjs",
    "w343t",
    "dfow4_112",
    "122.rwre",
    "56oer09gser9sdfd0s9dr333e",
    "12345678910",
    "test1",
    "test2",
    "test3",
    "test4",
    "7",
    "XX",
    "yyy",
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
    "test_4",
    "test_5",
    "test_6",
    "test_7",
    "test1",
    "test2",
    "test3",
    "test4",
    "baseA",
    "baseB",
    "testA",
    "testB",
    "testC",
  ];
  sample_ids.forEach((item_id) => {
    cy.deleteSampleViaAPI(item_id);
  });
  cy.visit("/");
  cy.wait(100);
  cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
});
