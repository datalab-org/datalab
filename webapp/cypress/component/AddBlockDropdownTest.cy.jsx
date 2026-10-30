import AddBlockDropdown from "@/components/AddBlockDropdown.vue";

const blockInfo = (id, name, available) => ({
  id,
  attributes: {
    name,
    description: `${name} description`,
    version: "1.0.0",
    accepted_file_extensions: [],
    available,
  },
});

describe("AddBlockDropdown", () => {
  it("only displays available block types", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        triggerTestid: "add-block-trigger",
        allBlockTypes: [
          blockInfo("comment", "Comment", true),
          blockInfo("xrd", "Powder XRD", false),
        ],
      },
    });

    cy.get('[data-testid="add-block-trigger"]').click();
    cy.contains("Comment").should("exist");
    cy.contains("Powder XRD").should("not.exist");
  });

  it("hides the control when no block types are available", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        triggerTestid: "add-block-trigger",
        allBlockTypes: [blockInfo("xrd", "Powder XRD", false)],
      },
    });

    cy.get('[data-testid="add-block-trigger"]').should("not.exist");
  });

  it("intersects global availability with the item type allowlist", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        triggerTestid: "add-block-trigger",
        blockTypeAllowList: ["comment", "media"],
        allBlockTypes: [
          blockInfo("comment", "Comment", true),
          blockInfo("media", "Media", false),
          blockInfo("xrd", "Powder XRD", true),
        ],
      },
    });

    cy.get('[data-testid="add-block-trigger"]').click();
    cy.contains("Comment").should("exist");
    cy.contains("Media").should("not.exist");
    cy.contains("Powder XRD").should("not.exist");
  });

  it("hides the control for an empty item type allowlist", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        triggerTestid: "add-block-trigger",
        blockTypeAllowList: [],
        allBlockTypes: [blockInfo("comment", "Comment", true)],
      },
    });

    cy.get('[data-testid="add-block-trigger"]').should("not.exist");
  });
});
