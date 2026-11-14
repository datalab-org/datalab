// E2e tests for the submit locking in Modal.vue: slow requests must only be sent once, and a
// failed submission must leave the modal usable for a retry. Needs the dev server + API (:5001)
// running in testing mode, with the tags feature enabled (PYDATALAB_ENABLE_TAGS).

const API_URL = Cypress.config("apiUrl");
const adminEmail = "admin-user@datalab.test";
const userEmail = "test-user@datalab.test";
const RESPONSE_DELAY_MS = 1500;

function delayResponses(method, path, alias) {
  cy.intercept(method, `${API_URL}${path}`, (req) => {
    req.on("response", (res) => {
      res.setDelay(RESPONSE_DELAY_MS);
    });
  }).as(alias);
}

function deleteGroupByIdViaAPI(groupId) {
  cy.request({ method: "GET", url: `${API_URL}/groups`, failOnStatusCode: false }).then(
    (response) => {
      (response.body?.data ?? [])
        .filter((group) => group.group_id === groupId)
        .forEach((group) => {
          cy.request({
            method: "DELETE",
            url: `${API_URL}/groups/${group.immutable_id}`,
            failOnStatusCode: false,
          });
        });
    },
  );
}

describe("Modal submit locking (items and collections)", () => {
  const sampleId = "e2e-double-submit-sample";
  const retrySampleId = "e2e-retry-submit-sample";
  const collectionId = "e2e-enter-submit-collection";

  beforeEach(() => {
    cy.loginViaTestMagicLink(userEmail);
    cy.deleteSampleViaAPI(sampleId);
    cy.deleteSampleViaAPI(retrySampleId);
    cy.deleteCollectionViaAPI(collectionId);
  });

  after(() => {
    cy.loginViaTestMagicLink(userEmail);
    cy.deleteSampleViaAPI(sampleId);
    cy.deleteSampleViaAPI(retrySampleId);
    cy.deleteCollectionViaAPI(collectionId);
  });

  it("creates a single sample when Submit is clicked twice during a slow request", () => {
    delayResponses("POST", "/new-sample/", "newSample");
    cy.visit("/");
    cy.findByText("Add an item").click();
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type(sampleId);
      cy.get("input[type=submit]").click();
      cy.get("input[type=submit]").should("be.disabled");
      cy.get("input[type=submit]").click({ force: true });
    });

    cy.wait("@newSample");
    cy.get('[data-testid="create-item-form"] .modal').should("not.be.visible");
    cy.get("@newSample.all").should("have.length", 1);
    cy.get("[data-testid=sample-table]").contains(sampleId).should("have.length", 1);
  });

  it("allows retrying after a failed submission without reopening the modal", () => {
    let attempts = 0;
    cy.intercept("POST", `${API_URL}/new-sample/`, (req) => {
      attempts += 1;
      if (attempts === 1) {
        req.reply({ statusCode: 500, body: { status: "error", message: "Simulated failure" } });
      }
    }).as("newSample");
    cy.visit("/");
    cy.findByText("Add an item").click();
    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.findByLabelText("ID:").type(retrySampleId);
      cy.get("input[type=submit]").click();
    });
    cy.wait("@newSample");
    cy.findByText("Creation Error").should("be.visible");
    cy.get('[data-testid="dialog-modal-confirm-button"]').click();

    cy.get('[data-testid="create-item-form"]').within(() => {
      cy.get("input[type=submit]").should("not.be.disabled").click();
    });
    cy.wait("@newSample").its("response.statusCode").should("eq", 201);
    cy.get("[data-testid=sample-table]").contains(retrySampleId).should("exist");
  });

  it("submits the create collection form with the Enter key, only once", () => {
    delayResponses("PUT", "/collections", "newCollection");
    cy.visit("/collections");
    cy.get('[data-testid="add-collection-button"]').click();
    cy.get("#collection-id").type(collectionId);
    cy.get(".modal-footer input[type=submit]:visible").should("not.be.disabled");
    cy.get("#collection-id").type("{enter}");
    cy.get(".modal-footer input[type=submit]:visible").should("be.disabled");
    cy.get("#collection-id").type("{enter}");

    cy.wait("@newCollection");
    cy.get("@newCollection.all").should("have.length", 1);
    cy.request(`${API_URL}/collections/${collectionId}`).its("status").should("eq", 200);
  });
});

describe("Modal submit locking (modals added since the PR)", () => {
  const tagName = "e2e-submit-tag";
  const otherTagName = "e2e-submit-other-tag";
  const groupId = "e2e-submit-group";

  beforeEach(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
    cy.deleteTagByNameViaAPI(otherTagName);
    deleteGroupByIdViaAPI(groupId);
  });

  after(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
    cy.deleteTagByNameViaAPI(otherTagName);
    deleteGroupByIdViaAPI(groupId);
  });

  it("re-enables the tag form after a name conflict so it can be resubmitted", () => {
    cy.createTagViaAPI({ name: tagName, scope: "global" });
    cy.visit("/tags");
    cy.get('[data-testid="add-tag-button"]').click();
    cy.get('[data-testid="tag-scope-select"]').select("global");
    cy.get("#tag-name").type(tagName);
    cy.get(".modal-footer input[type=submit]:visible").click();
    cy.get('[data-testid="tag-form"]').contains("already exists").should("be.visible");

    cy.get("#tag-name").clear();
    cy.get("#tag-name").type(otherTagName);
    cy.get(".modal-footer input[type=submit]:visible").should("not.be.disabled").click();
    cy.get('[data-testid="tag-form"] .modal').should("not.be.visible");
    cy.contains(".badge", otherTagName).should("exist");
  });

  it("creates a single group when Submit is clicked twice during a slow request", () => {
    delayResponses("PUT", "/groups", "newGroup");
    cy.visit("/admin");
    cy.contains(".sidebar li", "Groups").click();
    cy.contains("button", "Create Group").click();
    cy.get('[data-testid="create-group-form"]').within(() => {
      cy.get("#group-id").type(groupId);
      cy.get("#display-name").type("E2E submit group");
      cy.get("input[type=submit]").click();
      cy.get("input[type=submit]").should("be.disabled");
      cy.get("input[type=submit]").click({ force: true });
    });

    cy.wait("@newGroup");
    cy.get("@newGroup.all").should("have.length", 1);
    cy.get('[data-testid="create-group-form"] .modal').should("not.be.visible");
  });
});
