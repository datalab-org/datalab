import AddBlockDropdown from "@/components/AddBlockDropdown.vue";

const blockInfo = (id, name) => ({
  id,
  attributes: {
    name,
    description: `${name} description`,
    version: "1.0.0",
    accepted_file_extensions: [],
  },
});

describe("AddBlockDropdown", () => {
  it("displays the block types it is given", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        triggerTestid: "add-block-trigger",
        allBlockTypes: [blockInfo("comment", "Comment")],
      },
    });

    cy.get('[data-testid="add-block-trigger"]').click();
    cy.contains("Comment").should("exist");
  });

  it("disables the control with an explanatory tooltip", () => {
    cy.mount(AddBlockDropdown, {
      props: {
        variant: "button",
        triggerTestid: "add-block-trigger",
        menuTestid: "add-block-menu",
        allBlockTypes: [],
        disabled: true,
      },
    });

    cy.get('[data-testid="add-block-trigger"]').should("be.disabled");
    cy.get('[data-testid="add-block-trigger"]')
      .parent()
      .should(
        "have.attr",
        "title",
        "No block types are available for this item type on this deployment",
      );
    cy.get('[data-testid="add-block-menu"]').should("not.have.class", "show");
  });
});
