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

Cypress.Commands.add(
  "createSample",
  (item_id, name = null, date = null, generate_id_automatically = false) => {
    cy.findByText("Add an item").click();
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByText("Add new item").should("exist");
      cy.findByLabelText("ID:").type(item_id);
      if (name) {
        cy.findByLabelText("Name:").type(name);
      }
      if (date) {
        cy.findByLabelText("Date Created:").type(date);
      }
      if (generate_id_automatically) {
        cy.findByLabelText("generate automatically").click();
      }
      cy.findByText("Submit").click();
    });
  },
);

Cypress.Commands.add("verifySample", (item_id, name = null, date = null) => {
  cy.get("[data-testid=sample-table]")
    .contains(item_id)
    .parents("tr")
    .within(() => {
      if (date) {
        cy.contains(date.slice(0, 8));
      } else {
        cy.contains(TODAY.split("T")[0]);
      }
      if (name) {
        cy.contains(name);
      }
    });
});

Cypress.Commands.add("deleteSample", (item_id) => {
  cy.log("search for and delete: " + item_id);
  cy.get("[data-testid=sample-table]")
    .contains(new RegExp("^" + item_id + "$", "g"))
    .parents("tr")
    .find("button.close")
    .click();

  cy.get("[data-testid=sample-table]")
    .contains(new RegExp("^" + item_id + "$", "g"))
    .should("not.exist");
});

Cypress.Commands.add("deleteSampleViaAPI", (item_id) => {
  cy.log("search for and delete: " + item_id);
  cy.request({
    method: "POST",
    url: API_URL + "/delete-sample/",
    body: { item_id: item_id },
    failOnStatusCode: false,
  });
});

Cypress.Commands.add("searchAndSelectItem", (search_text, selector, clickPlus = false) => {
  // searches in the dropdown for the first real item with the given name, looking for a badge
  // if clickPlus, then also click the add row button before looking for the search bar
  if (clickPlus) {
    cy.get("#synthesis-information svg.add-row-button").click();
  }
  cy.get(selector).first().type(search_text);
  cy.get(".vs__dropdown-menu").contains(".badge", search_text).click();
});

Cypress.Commands.add("createEquipment", (item_id, name = null, date = null) => {
  cy.findByText("Add an item").click();
  cy.get('[data-testid="create-equipment-form"]').within(() => {
    cy.findByText("Add equipment").should("exist");
    cy.findByLabelText("ID:").type(item_id);
    if (name) {
      cy.findByLabelText("Name:").type(name);
    }
    if (date) {
      cy.findByLabelText("Date Created:").type(date);
    }
    cy.findByText("Submit").click();
  });
});

Cypress.Commands.add("verifyEquipment", (item_id, name = null, date = null, location = null) => {
  cy.get("[data-testid=equipment-table]")
    .contains(item_id)
    .parents("tr")
    .within(() => {
      if (date) {
        cy.contains(date.slice(0, 8));
      } else {
        cy.contains(TODAY.split("T")[0]);
      }
      if (name) {
        cy.contains(name);
      }
      if (location) {
        cy.contains(location);
      }
    });
});

Cypress.Commands.add("removeAllTestSamples", (item_ids, check_sample_table) => {
  // as contains matches greedily, if any IDs have matching substrings they must be added in the appropriate order
  item_ids = item_ids || [
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
  item_ids.forEach((item_id) => {
    cy.deleteSampleViaAPI(item_id);
  });
  if (check_sample_table) {
    cy.visit("/old-sample").then(() => {
      cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
    });
  }
});
