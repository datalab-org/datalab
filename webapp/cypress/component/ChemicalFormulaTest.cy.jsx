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

  it("handles case sensitivity correctly", () => {
    cy.get("input").type("CH4");
    cy.get("input").should("have.value", "CH<sub>4</sub>");
  });

  it("renders single element with subscript correctly", () => {
    cy.get("input").type("Na3P");
    cy.get("input").should("have.value", "Na<sub>3</sub>P");
  });

  it("renders formula with charges correctly", () => {
    cy.get("input").type("Na+Cl-");
    cy.get("input").should("have.value", "Na<sup>+</sup>Cl<sup>-</sup>");
  });

  it("renders formula with multiple charges correctly", () => {
    cy.get("input").type("Ca++SO4--");
    cy.get("input").should("have.value", "Ca<sup>2+</sup>SO<sub>4</sub><sup>2-</sup>");
  });

  it("renders hydrated compounds correctly", () => {
    cy.get("input").type("Cu2SO4.H2O");
    cy.get("input").should("have.value", "Cu<sub>2</sub>SO<sub>4</sub>·H<sub>2</sub>O");
  });

  it("renders complex formula with variables correctly", () => {
    cy.get("input").type("Na3+xP");
    cy.get("input").should("have.value", "Na<sub>3+x</sub>P<sub>4</sub>");
  });

  it("handles empirical formula units correctly", () => {
    cy.get("input").type("[pyr]");
    cy.get("input").should("have.value", "[pyr]");
  });

  it("renders parentheses with subscripts correctly", () => {
    cy.get("input").type("(NH4)2SO4");
    cy.get("input").should("have.value", "(NH<sub>4</sub>)<sub>2</sub>SO<sub>4</sub>");
  });

  it("renders formula with Greek letters correctly", () => {
    cy.get("input").type("α-Fe2O3");
    cy.get("input").should("have.value", "&alpha;-Fe<sub>2</sub>O<sub>3</sub>");
  });

  it("renders formula with multiple Greek letters correctly", () => {
    cy.get("input").type("β-Li3PO4");
    cy.get("input").should("have.value", "&beta;-Li<sub>3</sub>PO<sub>4</sub>");
  });

  it("renders formula with uppercase Greek letters correctly", () => {
    cy.get("input").type("Δ-MnO2");
    cy.get("input").should("have.value", "&Delta;-MnO<sub>2</sub>");
  });

  it("handles complex formula with Greek letters and charges", () => {
    cy.get("input").type("α-Li+β-FePO4-");
    cy.get("input").should(
      "have.value",
      "&alpha;-Li<sup>+</sup>&beta;-FePO<sub>4</sub><sup>-</sup>",
    );
  });

  it("handles formula with variables and Greek letters", () => {
    cy.get("input").type("Li1+xMnα2O4");
    cy.get("input").should("have.value", "Li<sub>1+x</sub>Mn&alpha;<sub>2</sub>O<sub>4</sub>");
  });

  it("preserves unknown symbols when mixed with valid chemistry", () => {
    cy.get("input").type("CH4@SiO2");
    cy.get("input").should("have.value", "CH<sub>4</sub>@SiO<sub>2</sub>");
  });

  it("handles decimal subscripts correctly", () => {
    cy.get("input").type("Li1.2Mn2O4");
    cy.get("input").should("have.value", "Li<sub>1.2</sub>Mn<sub>2</sub>O<sub>4</sub>");
  });

  it("handles multiple elements and subscripts correctly", () => {
    cy.get("input").type("Na3P4");
    cy.get("input").should("have.value", "Na<sub>3</sub>P<sub>4</sub>");
  });

  it("handles mixed parentheses and subscripts", () => {
    cy.get("input").type("(NaLi)3P");
    cy.get("input").should("have.value", "(NaLi)<sub>3</sub>P");
  });

  it("handles invalid input gracefully", () => {
    cy.get("input").type("Invalid@Formula#123");
    cy.get("input").should("have.value", "Invalid@Formula#123");
  });

  it("handles empty input gracefully", () => {
    cy.get("input").clear();
    cy.get("input").should("have.value", "");
  });

  it("handles complex hydrated compounds", () => {
    cy.get("input").type("CuSO4.5H2O");
    cy.get("input").should("have.value", "CuSO<sub>4</sub>·<sub>5</sub>H<sub>2</sub>O");
  });

  it("handles charges with numbers", () => {
    cy.get("input").type("Fe3+Cl3-");
    cy.get("input").should("have.value", "Fe<sub>3</sub><sup>+</sup>Cl<sub>3</sub><sup>-</sup>");
  });
});
