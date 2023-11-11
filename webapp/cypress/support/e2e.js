// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import "./commands";

// Alternatively you can use CommonJS syntax:
// require('./commands')
const TODAY = new Date().toISOString().slice(0, -8);

export function createSample(sample_id, name = null, date = null) {
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

export function verifySample(sample_id, name = null, date = null) {
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

export function removeAllTestSamples(sample_ids) {
  // as contains matches greedily, if any IDs have matching substrings they must be added in the appropriate order
  sample_ids.forEach((item_id) => {
    deleteSample(item_id);
  });
  cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
}

export function deleteSample(sample_id, delay = 100) {
  cy.visit("/");
  cy.wait(delay).then(() => {
    cy.log("search for and delete: " + sample_id);
    cy.get("[data-testid=sample-table]")
      .contains(sample_id)
      .parents("tr")
      .within(() => {
        cy.get("button.close").click();
      });
  });
}

export function searchAndSelectItem(search_text, selector, delay = 100) {
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
