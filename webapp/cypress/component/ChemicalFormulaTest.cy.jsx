import { ChemFormulaInput } from "@components/ChemFormulaInput.vue";

describe("ChemFormulaInput", () => {
  beforeEach(() => {
    cy.mount(ChemFormulaInput);
  });

  it("renders single element formula correctly", () => {
    cy.get("input").type("Na");
    cy.get(".formula").should("contain", "Na");
  });

  it("renders single element with subscript correctly", () => {
    cy.get("input").type("Na3");
    cy.get(".formula").should("contain", "Na<sub>3</sub>");
  });

  it("renders formula with parentheses correctly", () => {
    cy.get("input").type("Na3P");
    cy.get(".formula").should("contain", "Na<sub>3</sub>P");
  });

  it("renders formula with multiple elements in parentheses correctly", () => {
    cy.get("input").type("(NaLi)3P");
    cy.get(".formula").should("contain", "(NaLi)<sub>3</sub>P");
  });

  it("renders formula with multiple elements and subscripts correctly", () => {
    cy.get("input").type("Na3P4");
    cy.get(".formula").should("contain", "Na<sub>3</sub>P<sub>4</sub>");
  });

  it("handles invalid input gracefully", () => {
    cy.get("input").type("Invalid@Formula");
    cy.get(".formula").should("contain", "InFo");
  });
});
