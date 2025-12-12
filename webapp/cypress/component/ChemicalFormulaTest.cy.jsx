import ChemicalFormula from "@/components/ChemicalFormula.vue";

describe("ChemicalFormula", () => {
  it("renders single element formula correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na" } });
    cy.get("span").should("contain", "Na");
  });

  it("renders single element with subscript correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na3P" } });
    cy.get("span").should("contain.html", "Na<sub>3</sub>P");
  });

  it("renders formula with multiple elements and subscripts correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na3P4" } });
    cy.get("span").should("contain.html", "Na<sub>3</sub>P<sub>4</sub>");
  });

  it("renders formula with parentheses correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Ca(OH)2" } });
    cy.get("span").should("contain.html", "Ca(OH)<sub>2</sub>");
  });

  it("renders formula with multiple elements in parentheses correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "(NaLi)3P" } });
    cy.get("span").should("contain.html", "(NaLi)<sub>3</sub>P");
  });

  it("renders hydrate formula with interpunct correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Cu2SO4.H2O" } });
    cy.get("span").should("contain.html", "Cu<sub>2</sub>SO<sub>4</sub> · H<sub>2</sub>O");
  });

  it("renders formula with variables correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na3+xP" } });
    cy.get("span").should("contain.html", "Na<sub>3+x</sub>P");
  });

  it("renders charged ions correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na+" } });
    cy.get("span").should("contain.html", "Na<sup>+</sup>");
  });

  it("renders negatively charged ions correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Cl-" } });
    cy.get("span").should("contain.html", "Cl<sup>-</sup>");
  });

  it("renders formula with multiple charges correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Ca2+" } });
    cy.get("span").should("contain.html", "Ca<sup>2+</sup>");
  });

  it("handles empirical shorthand units correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "[pyr]" } });
    cy.get("span").should("contain.html", "[pyr]");
  });

  it("handles complex formula with empirical units", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li[pyr]3" } });
    cy.get("span").should("contain.html", "Li[pyr]<sub>3</sub>");
  });

  it("handles invalid input gracefully", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Invalid@Formula" } });
    cy.get("span").should("contain.html", "Invalid@Formula");
  });

  it("handles decimal subscripts correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "LiNi0.8Co0.1Mn0.1O2" } });
    cy.get("span").should(
      "contain.html",
      "LiNi<sub>0.8</sub>Co<sub>0.1</sub>Mn<sub>0.1</sub>O<sub>2</sub>",
    );
  });

  it("handles Greek letter alpha correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li-α-NMC" } });
    cy.get("span").should("contain", "Li-α-NMC");
  });

  it("handles Greek letter beta in formula correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "β-Li3N" } });
    cy.get("span").should("contain.html", "β-Li<sub>3</sub>N");
  });

  it("handles Greek letter gamma phase correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "γ-Fe2O3" } });
    cy.get("span").should("contain.html", "γ-Fe<sub>2</sub>O<sub>3</sub>");
  });

  it("handles multiple Greek letters correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "α-β-γ-Al2O3" } });
    cy.get("span").should("contain.html", "α-β-γ-Al<sub>2</sub>O<sub>3</sub>");
  });

  it("handles delta phase with subscripts", () => {
    cy.mount(ChemicalFormula, { props: { formula: "δ-MnO2" } });
    cy.get("span").should("contain.html", "δ-MnO<sub>2</sub>");
  });

  it("handles prime notation correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li′" } });
    cy.get("span").should("contain", "Li′");
  });

  it("handles middle dot correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Cu2SO4∙H2O" } });
    cy.get("span").should("contain.html", "Cu<sub>2</sub>SO<sub>4</sub> · H<sub>2</sub>O");
  });

  it("handles uppercase Greek letters correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Δ-MnO2" } });
    cy.get("span").should("contain.html", "Δ-MnO<sub>2</sub>");
  });

  it("handles fractional subscripts correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "LiNi1/3Mn1/3Co1/3O2" } });
    cy.get("span").should(
      "contain.html",
      "LiNi<sub>1/3</sub>Mn<sub>1/3</sub>Co<sub>1/3</sub>O<sub>2</sub>",
    );
  });

  it("handles mixture notation with slashes correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "NMC/C" } });
    cy.get("span").should("contain.html", "NMC/C");
  });

  it("handles complex mixture with formula and slash", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li2O/graphite" } });
    cy.get("span").should("contain.html", "Li<sub>2</sub>O/graphite");
  });

  it("preserves explicit subscript tags", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na<sub>x</sub>CoO2" } });
    cy.get("span").should("contain.html", "Na<sub>x</sub>CoO<sub>2</sub>");
  });

  it("preserves explicit superscript tags", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Na<sup>+</sup>Cl<sup>-</sup>" } });
    cy.get("span").should("contain.html", "Na<sup>+</sup>Cl<sup>-</sup>");
  });

  it("handles mixed explicit tags and auto-formatting", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li<sub>1-x</sub>Ni0.8Co0.2O2" } });
    cy.get("span").should(
      "contain.html",
      "Li<sub>1-x</sub>Ni<sub>0.8</sub>Co<sub>0.2</sub>O<sub>2</sub>",
    );
  });

  it("handles fractions with multiple elements correctly", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Li1/2Mn1/2O2" } });
    cy.get("span").should("contain.html", "Li<sub>1/2</sub>Mn<sub>1/2</sub>O<sub>2</sub>");
  });

  it("handles mixed fractions and decimals", () => {
    cy.mount(ChemicalFormula, { props: { formula: "LiNi1/3Co0.1Mn0.1O2" } });
    cy.get("span").should(
      "contain.html",
      "LiNi<sub>1/3</sub>Co<sub>0.1</sub>Mn<sub>0.1</sub>O<sub>2</sub>",
    );
  });

  it("handles slash at start for phase notation", () => {
    cy.mount(ChemicalFormula, { props: { formula: "α-NMC/C/binder" } });
    cy.get("span").should("contain.html", "α-NMC/C/binder");
  });

  it("handles complex formula with all features", () => {
    cy.mount(ChemicalFormula, {
      props: { formula: "Li<sub>1-x</sub>Ni1/3Mn1/3Co1/3O2/graphite" },
    });
    cy.get("span").should(
      "contain.html",
      "Li<sub>1-x</sub>Ni<sub>1/3</sub>Mn<sub>1/3</sub>Co<sub>1/3</sub>O<sub>2</sub>/graphite",
    );
  });

  it("preserves multiple explicit tags in sequence", () => {
    cy.mount(ChemicalFormula, { props: { formula: "Ca<sup>2+</sup>(OH)<sub>2</sub>" } });
    cy.get("span").should("contain.html", "Ca<sup>2+</sup>(OH)<sub>2</sub>");
  });
});
