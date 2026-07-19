// E2e tests for the tag management page (/tags). Needs the dev server + API (:5001) running
// with testing auth AND the tags feature enabled (PYDATALAB_ENABLE_TAGS).
// Tags are global and admin-only; admin-user@example.com is an admin by the same
// convention as authenticatedSampleTests.cy.js.

const adminEmail = "admin-user@example.com";
const userEmail = "tag-owner@example.com"; // a non-admin user

describe("Tag management page (admin)", () => {
  // Names must not be substrings of each other: cy.contains matches substrings, so a
  // "not.exist" check on the original would still match the renamed badge otherwise.
  const tagName = "e2e-create-tag";
  const renamedTag = "e2e-renamed-tag";

  beforeEach(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
    cy.deleteTagByNameViaAPI(renamedTag);
  });

  after(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
    cy.deleteTagByNameViaAPI(renamedTag);
  });

  it("creates, edits and deletes a tag", () => {
    cy.visit("/tags");

    // Create
    cy.get('[data-testid="add-tag-button"]').click();
    cy.get("#tag-name").type(tagName);
    cy.get("#tag-description").type("created in an e2e test");
    cy.get(".swatch").first().click();
    cy.get(".modal-footer input[type=submit]:visible").click();
    // Scope badge assertions to the table: the (closed) edit/create modal keeps a hidden
    // TagBadge preview in the DOM (Modal uses display:none), which a document-wide
    // `.badge` match would pick up and break the `not.exist` checks below.
    cy.get('[data-testid="tags-table"]').contains(".badge", tagName).should("exist");

    // Edit (rename)
    cy.contains("tr", tagName).find('button[title="Edit tag"]').click();
    cy.get("#tag-name").clear();
    cy.get("#tag-name").type(renamedTag);
    cy.get(".modal-footer input[type=submit]:visible").click();
    cy.get('[data-testid="tags-table"]').contains(".badge", renamedTag).should("exist");
    cy.get('[data-testid="tags-table"]').contains(".badge", tagName).should("not.exist");

    // Delete
    cy.contains("tr", renamedTag).find('button[title="Delete tag"]').click();
    cy.get('[data-testid="dialog-modal-confirm-button"]').click();
    cy.get('[data-testid="tags-table"]').contains(".badge", renamedTag).should("not.exist");
  });
});

describe("Tag management permissions", () => {
  const tagName = "e2e-perm-tag";

  before(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
    cy.createTagViaAPI({ name: tagName });
  });

  after(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(tagName);
  });

  it("hides create/edit/delete controls for a non-admin", () => {
    cy.loginViaTestMagicLink(userEmail);
    cy.visit("/tags");
    cy.contains("tr", tagName).should("exist"); // the table is visible to everyone
    cy.get('[data-testid="add-tag-button"]').should("not.exist");
    cy.contains("tr", tagName).within(() => {
      cy.get('button[title="Edit tag"]').should("not.exist");
      cy.get('button[title="Delete tag"]').should("not.exist");
    });
  });

  it("shows create/edit/delete controls for an admin", () => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.visit("/tags");
    cy.get('[data-testid="add-tag-button"]').should("exist");
    cy.contains("tr", tagName).within(() => {
      cy.get('button[title="Edit tag"]').should("exist");
    });
  });
});

describe("Applying a tag to an item", () => {
  const intTag = "e2e-applied-tag";
  const sampleId = "e2e-tag-sample";

  before(() => {
    // Only admins can create tags.
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(intTag);
    cy.createTagViaAPI({ name: intTag });
  });

  beforeEach(() => {
    cy.loginViaTestMagicLink(userEmail);
    cy.deleteSampleViaAPI(sampleId);
    cy.visit("/samples");
    cy.createSample(sampleId, "Tag e2e sample");
  });

  after(() => {
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteSampleViaAPI(sampleId);
    cy.deleteTagByNameViaAPI(intTag);
  });

  it("applies a tag and drops it from the item when the tag is deleted", () => {
    cy.intercept("GET", "**/search-tags*").as("searchTags");
    cy.intercept("POST", "**/save-item/").as("save");

    cy.visit(`/edit/${sampleId}`);

    // Enter edit mode on the Tags field (click the label text, away from the cog link),
    // then pick the tag from the TagSelect dropdown.
    cy.get("#tags").click("left");
    cy.get("#tags").parent().find(".vs__search").type(intTag);
    cy.wait("@searchTags");
    cy.get("#tags").parent().contains(".vs__dropdown-option", intTag).click();

    // Save (Ctrl/Cmd+S) and confirm the tag survives a reload.
    cy.get("body").type("{ctrl}s");
    cy.wait("@save");
    cy.reload();
    cy.contains(".badge", intTag).should("exist");

    // Deleting the tag (as admin) removes the reference from the item on the next read.
    cy.loginViaTestMagicLink(adminEmail);
    cy.deleteTagByNameViaAPI(intTag);
    cy.loginViaTestMagicLink(userEmail);
    cy.reload();
    cy.contains(".badge", intTag).should("not.exist");
  });
});
