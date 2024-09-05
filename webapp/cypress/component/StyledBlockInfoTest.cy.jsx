import StyledBlockInfo from "@/components/StyledBlockInfo.vue";

describe("StyledBlockInfo", () => {
  const blockInfo = {
    attributes: {
      name: "Example Block",
      description: "This is an example block description.",
      accepted_file_extensions: [".pdf", ".docx", ".xlsx"],
    },
  };

  it("renders the tooltip with correct content on hover", () => {
    cy.mount(StyledBlockInfo, {
      propsData: { blockInfo },
    });

    cy.get("a").trigger("mouseenter", { force: true });

    cy.get("#tooltip")
      .should("be.visible")
      .within(() => {
        cy.contains(blockInfo.attributes.name).should("be.visible");
        cy.contains(blockInfo.attributes.description).should("be.visible");
        cy.contains(".pdf").should("be.visible");
        cy.contains(".docx").should("be.visible");
        cy.contains(".xlsx").should("be.visible");
      });
  });

  it("hides the tooltip on mouseleave", () => {
    cy.mount(StyledBlockInfo, {
      propsData: { blockInfo },
    });

    cy.get("a").trigger("mouseenter", { force: true });
    cy.get("a").trigger("mouseleave", { force: true });

    cy.get("#tooltip").should("not.have.attr", "data-show");
  });

  it("shows and hides tooltip on focus and blur", () => {
    cy.mount(StyledBlockInfo, {
      propsData: { blockInfo },
    });

    cy.get("a").focus();
    cy.get("#tooltip").should("be.visible");

    cy.get("a").blur();
    cy.get("#tooltip").should("not.have.attr", "data-show");
  });
});
