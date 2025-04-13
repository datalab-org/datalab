import ChemFormulaInput from "@/components/ChemFormulaInput.vue";

describe("ChemFormulaInput", () => {
  beforeEach(() => {
    cy.mount(ChemFormulaInput);
    cy.get("span").click({ force: true });
  });

  it("renders single element formula correctly", () => {
    cy.get("input").type("Na");
    cy.get("input").should("have.value", "Na");
  });

  it("renders single element with subscript correctly", () => {
    cy.get("input").type("Na3P");
    cy.get("input").should("have.value", "Na<sub>3</sub>P");
  });

  // it("renders formula with parentheses correctly", () => {
  //   cy.get("input").type("Na3P");
  // cy.get("input").should("have.value", "Na<sub>3</sub>P");
  // });

  // it("renders formula with multiple elements in parentheses correctly", () => {
  //   cy.get("input").type("(NaLi)3P");
  //   cy.get("input").should("have.value", "(NaLi)<sub>3</sub>P");
  // });

  // it("renders formula with multiple elements and subscripts correctly", () => {
  //   cy.get("input").type("Na3P4");
  //   cy.get("input").should("have.value", "Na<sub>3</sub>P<sub>4</sub>");
  // });

  // it("renders formula with multiple elements and subscripts correctly", () => {
  //   cy.get("input").type("Cu2SO4.H2O");
  //   cy.get("input").should("have.value", "Cu<sub>2</sub>SO<sub>4</sub>·H<sub>2</sub>O");
  // });

  // it("handles empirical shorthand units correctly", () => {
  //   cy.get("input").type("[pyr]");
  //   cy.get("input").should("have.value", "[pyr]");
  // });

  // it("handles charges and subscripts", () => {
  //   cy.get("input").type("[pyr]");
  //   cy.get("input").should("have.value", "[pyr]");
  // });

  // it("handles invalid input gracefully", () => {
  //   cy.get("input").type("Invalid@Formula");
  //   cy.get("input").should("have.value", "Invalid@Formula");
  // });
});
