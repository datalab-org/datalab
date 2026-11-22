const ITEM_ID = "timeline_sample";
const XRD_FILE = "example_data/XRD/Scan_C8.xrdml";
const XRD_FILENAME = "example_data_XRD_Scan_C8.xrdml";

const expectBlockOrder = (expectedIds) =>
  cy
    .get(".block-container .data-block")
    .should(($blocks) => expect([...$blocks].map((b) => b.id)).to.deep.equal(expectedIds()));

before(() => {
  cy.loginViaTestMagicLink("test-user@datalab.test");
  cy.visit("/");
  cy.removeAllTestSamples([ITEM_ID], true);
});

after(() => {
  cy.loginViaTestMagicLink("test-user@datalab.test");
  cy.visit("/");
  cy.removeAllTestSamples([ITEM_ID], true);
  cy.logout();
});

describe("Block timeline ordering", () => {
  let commentBlockId;
  let xrdBlockId;

  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@datalab.test");
    cy.visit("/");
  });

  it("creates a sample with a comment block and a dated XRD block", () => {
    cy.createSample(ITEM_ID, "Timeline sample");
    cy.uploadFileViaAPI(ITEM_ID, XRD_FILE);

    cy.get('[data-testid="search-input"]').type(ITEM_ID);
    cy.findByText(ITEM_ID).click();

    cy.get('[data-testid="block-order-toggle"]').should("not.exist");

    cy.addBlockFromTopDropdown("Comment").then(($block) => {
      commentBlockId = $block.attr("id");
    });
    cy.get('[data-testid="block-order-toggle"]').should("not.exist");

    cy.addBlockFromTopDropdown("Powder XRD").then(($block) => {
      xrdBlockId = $block.attr("id");
    });
    cy.get(".multi-file-selector").contains(XRD_FILENAME).dblclick();
    cy.then(() =>
      cy
        .get(`[id="${xrdBlockId}"] [data-testid="block-provenance"]`)
        .should("contain", "Measured")
        .and("contain", "2020"),
    );

    cy.get(".fa-save").click();
    cy.contains("Unsaved changes").should("not.exist");
  });

  it("switches between manual and timeline order, remembering the choice", () => {
    cy.get('[data-testid="search-input"]').type(ITEM_ID);
    cy.findByText(ITEM_ID).click();

    cy.get('[data-testid="block-order-toggle"]').should("contain", "Manual");
    cy.get('[data-testid="block-timeline"]').should("not.exist");
    expectBlockOrder(() => [commentBlockId, xrdBlockId]);

    cy.get('[data-testid="block-order-toggle"]').contains("Timeline").click();
    cy.get('[data-testid="block-timeline"]').should("exist");
    expectBlockOrder(() => [xrdBlockId, commentBlockId]);
    cy.get('[data-testid="timeline-divider"]').should("have.length", 2);
    cy.get('[data-testid="timeline-divider"]').first().should("contain", "2020");
    cy.get(".block-container .datablock-header .fa-arrow-up").should("not.exist");
    cy.get(".block-container .datablock-header .fa-arrow-down").should("not.exist");

    cy.reload();
    cy.get('[data-testid="block-timeline"]').should("exist");
    expectBlockOrder(() => [xrdBlockId, commentBlockId]);

    cy.get('[data-testid="block-order-toggle"]').contains("Manual").click();
    cy.get('[data-testid="block-timeline"]').should("not.exist");
    expectBlockOrder(() => [commentBlockId, xrdBlockId]);
    cy.get(".block-container .datablock-header .fa-arrow-down").should("exist");
  });
});
