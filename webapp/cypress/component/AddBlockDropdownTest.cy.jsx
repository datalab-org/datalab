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
});
