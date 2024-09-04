import StyledBlockHelp from "@/components/StyledBlockHelp.vue";

describe("StyledBlockHelp Component", () => {
  const blockInfo = {
    name: "Sample Block",
    description: "This is a sample block description.",
    accepted_file_extensions: [".jpg", ".png", ".gif"],
  };

  it("renders the tooltip with correct content on hover", () => {
    cy.mount(StyledBlockHelp, {
      propsData: { blockInfo },
    });

    cy.get("a.dropdown-item").trigger("mouseenter");

    cy.get("#tooltip")
      .should("be.visible")
      .within(() => {
        cy.contains(blockInfo.description).should("be.visible");
        cy.contains("Accepted file extensions:").should("be.visible");
        cy.contains(".jpg, .png, .gif").should("be.visible");
      });
  });

  it("hides the tooltip on mouseleave", () => {
    cy.mount(StyledBlockHelp, {
      propsData: { blockInfo },
    });

    cy.get("a.dropdown-item").trigger("mouseenter");
    cy.get("a.dropdown-item").trigger("mouseleave");

    cy.get("#tooltip").should("not.have.attr", "data-show");
  });

  it("shows and hides tooltip on focus and blur", () => {
    cy.mount(StyledBlockHelp, {
      propsData: { blockInfo },
    });

    cy.get("a.dropdown-item").focus();
    cy.get("#tooltip").should("be.visible");

    cy.get("a.dropdown-item").blur();
    cy.get("#tooltip").should("not.have.attr", "data-show");
  });
});
