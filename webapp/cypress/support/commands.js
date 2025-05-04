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

Cypress.Commands.add("selectItemCheckbox", (type, item_id) => {
  cy.get(`[data-testid=${type}-table]`)
    .contains(new RegExp("^" + item_id + "$", "g"))
    .parents("tr")
    .find("input[type='checkbox']")
    .click();
});

Cypress.Commands.add("deleteItems", (type, items_id) => {
  cy.log("search for and delete: " + items_id);
  items_id.forEach((item_id) => {
    cy.selectItemCheckbox(type, item_id);
  });

  cy.get('[data-testid="selected-dropdown"]').click();
  cy.get('[data-testid="delete-selected-button"]').click();

  cy.on("window:confirm", (text) => {
    expect(text).to.contains(items_id);
    return true;
  });

  items_id.forEach((item_id) => {
    cy.get(`[data-testid=${type}-table]`)
      .contains(new RegExp("^" + item_id + "$", "g"))
      .should("not.exist");
  });
});

Cypress.Commands.add("deleteCollectionViaAPI", (collection_id) => {
  cy.log("search for and delete: " + collection_id);
  cy.request({
    method: "DELETE",
    url: API_URL + "/collections/" + collection_id,
    failOnStatusCode: false,
  });
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

Cypress.Commands.add("uploadFileViaAPI", (itemId, path) => {
  cy.log("Upload a test file via the API: " + path);
  cy.fixture(path, "binary")
    .then(Cypress.Blob.binaryStringToBlob)
    .then((blob) => {
      const formData = new FormData();
      formData.append("relativePath", "null");
      formData.append("name", path);
      formData.append("type", "application/octet-stream");
      formData.append("size", blob.size.toString());
      formData.append("item_id", itemId);
      formData.append("replace_file", "null");
      formData.append("files[]", blob, path);

      return cy.request({
        method: "POST",
        url: API_URL + "/upload-file/",
        body: formData,
        headers: { "Content-Type": "multipart/form-data" },
        form: false,
      });
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
    cy.visit("/").then(() => {
      cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
    });
  }
});

Cypress.Commands.add("createTestPNG", (fname) => {
  const canvas = document.createElement("canvas");
  canvas.width = 100;
  canvas.height = 100;

  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ff0000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const base64 = canvas.toDataURL("image/png").split(",")[1];
  const filePath = `cypress/fixtures/${fname}`;

  return cy.writeFile(filePath, base64, "base64").then(() => {});
});

Cypress.Commands.add("removeAllTestCollections", (collection_ids, check_collection_table) => {
  collection_ids.forEach((collection_id) => {
    cy.deleteCollectionViaAPI(collection_id);
  });

  if (check_collection_table) {
    cy.visit("/collections").then(() => {
      // The test ID of the collection table is still 'sample table'
      cy.get("[data-testid=sample-table] > tbody > tr").should("have.length", 0);
    });
  }
});

Cypress.Commands.add("createStartingMaterial", (item_id, name = null, date = null) => {
  cy.findByText("Add a starting material").click();

  cy.get('[data-testid="create-item-form"]').within(() => {
    cy.findByText("Add new item").should("exist");
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

Cypress.Commands.add("verifyStartingMaterial", (item_id, name = null, date = null) => {
  cy.get("[data-testid=starting_materials-table]")
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

Cypress.Commands.add("expandIfCollapsed", (selector) => {
  cy.get(selector)
    .find("[data-testid=collapse-arrow]")
    .parents(".datablock-header")
    .then(($header) => {
      if (!$header.hasClass("expanded")) {
        cy.wrap($header).find("[data-testid=collapse-arrow]").click();
      }
    });
});
