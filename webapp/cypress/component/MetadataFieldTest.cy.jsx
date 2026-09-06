import MetadataField from "@/components/MetadataField.vue";

// Where a value came from decides what may be done to it, so these check that
// the menu offers what the block says it can and nothing else.
describe("MetadataField", () => {
  const mount = (entry) =>
    cy.mount(MetadataField, {
      propsData: { item_id: "test", block_id: "block", field: "sample_mass_mg", entry },
    });

  const fromFile = {
    value: 14.32,
    source: "file",
    bound: false,
    available: { file: 14.32, sample: null },
  };

  it("shows the value and where it came from", () => {
    mount(fromFile);

    cy.contains("14.32").should("be.visible");
    cy.get(".source").should("have.text", "file").and("have.attr", "title").and("include", "file");
  });

  it("marks a value somebody typed as theirs", () => {
    mount({ value: 99, source: "user", bound: true, available: { file: 14.32 } });

    cy.get(".source").should("have.text", "user supplied");
    cy.get(".source").should("have.attr", "title").and("include", "nothing will overwrite it");
  });

  it("shows an empty field rather than hiding it", () => {
    mount({ value: null, source: null, bound: false, available: { file: null } });

    cy.get(".value").should("have.text", "—").and("have.class", "empty");
  });

  it("offers only the sources that have something to offer", () => {
    mount(fromFile);
    cy.get(".metadata-field").rightclick();

    // `sample` has nothing, and `file` is already in use.
    cy.get(".dropdown-item").should("not.contain", "sample");
    cy.get(".dropdown-item").should("not.contain", "Use file value");
    cy.contains(".dropdown-item", "Override…").should("be.visible");
    cy.contains(".dropdown-item", "Set to empty").should("be.visible");
  });

  it("offers a source that did not win, with its value", () => {
    mount({ ...fromFile, available: { file: 14.32, sample: 21.4 } });
    cy.get(".metadata-field").rightclick();

    cy.contains(".dropdown-item", "Use sample value").should("contain", "21.4");
  });

  it("only offers to choose automatically once something has been chosen", () => {
    mount(fromFile);
    cy.get(".metadata-field").rightclick();
    cy.get(".dropdown-item").should("not.contain", "Choose automatically");

    mount({ ...fromFile, bound: true });
    cy.get(".metadata-field").rightclick();
    cy.contains(".dropdown-item", "Choose automatically").should("be.visible");
  });

  it("edits in place, starting from the value on show", () => {
    mount(fromFile);
    cy.get(".metadata-field").rightclick();
    cy.contains(".dropdown-item", "Override…").click();

    cy.get("input").should("be.focused").and("have.value", "14.32");
    cy.get("input").type("{esc}");
    cy.get(".value").should("have.text", "14.32");
  });
});
