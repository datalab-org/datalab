import MetadataField from "@/components/MetadataField.vue";

// Where a value came from decides what may be done to it, so these check that
// the menu offers what the block says it can and nothing else.
describe("MetadataField", () => {
  const mount = (entry) =>
    cy.mount(MetadataField, {
      propsData: {
        item_id: "test",
        block_id: "block",
        field: "sample_mass_mg",
        entry,
        sourceLabels: { file: "NiCl2btd_MT.rso.dat", sample: "NiCl2btd-01" },
      },
    });

  const fromFile = {
    value: 14.32,
    source: "file",
    bound: false,
    available: { file: 14.32, sample: null },
  };

  it("names the file a value was read out of, not just that it was read from one", () => {
    mount(fromFile);

    cy.contains("14.32").should("be.visible");
    cy.get(".source").should("have.text", "file");
    cy.get(".source").should("have.attr", "title", "Supplied by NiCl2btd_MT.rso.dat");
  });

  it("falls back to the source's own name where there is nothing better", () => {
    cy.mount(MetadataField, {
      propsData: { item_id: "test", block_id: "block", field: "sample_mass_mg", entry: fromFile },
    });

    cy.get(".source").should("have.attr", "title", "Supplied by file");
  });

  it("marks a value somebody typed as theirs", () => {
    mount({ value: 99, source: "user", bound: true, available: { file: 14.32 } });

    cy.get(".source").should("have.text", "user supplied");
    cy.get(".source").should("have.attr", "title", "Value overwritten by user");
  });

  it("names who made a choice, and when", () => {
    mount({
      value: 99,
      source: "user",
      bound: true,
      available: { file: 14.32 },
      set_by_name: "Ada Lovelace",
      set_at: "2026-09-05T18:30:00+00:00",
    });

    cy.get(".source")
      .should("have.attr", "title")
      .and("match", /^Value overwritten by Ada Lovelace on /);
  });

  it("attributes the choice of a source too, not only a typed value", () => {
    mount({
      value: 14.32,
      source: "file",
      bound: true,
      available: { file: 14.32, sample: 21.4 },
      set_by_name: "Ada Lovelace",
      set_at: "2026-09-05T18:30:00+00:00",
    });

    cy.get(".source")
      .should("have.attr", "title")
      .and("match", /^Supplied by NiCl2btd_MT\.rso\.dat, chosen by Ada Lovelace on /);
  });

  it("says only what it knows about a binding nobody is recorded for", () => {
    mount({ value: 99, source: "user", bound: true, available: {} });

    cy.get(".source").should("have.attr", "title", "Value overwritten by user");
  });

  it("says so when somebody has decided there is no value", () => {
    mount({ value: null, source: "user", bound: true, available: { file: 14.32 } });

    cy.get(".source").should("have.attr", "title", "Value set to blank by user");
  });

  it("shows an empty field rather than hiding it", () => {
    mount({ value: null, source: null, bound: false, available: { file: null } });

    cy.get(".value").should("have.text", "—").and("have.class", "empty");
  });

  it("offers only the sources that have something to offer", () => {
    mount(fromFile);
    cy.get(".metadata-field").click();

    // `sample` has nothing, and `file` is already in use.
    cy.get(".dropdown-item").should("not.contain", "sample");
    cy.get(".dropdown-item").should("not.contain", "Use file value");
    cy.contains(".dropdown-item", "Override…").should("be.visible");
    cy.contains(".dropdown-item", "Set to empty").should("be.visible");
  });

  it("offers a source that did not win, with its value", () => {
    mount({ ...fromFile, available: { file: 14.32, sample: 21.4 } });
    cy.get(".metadata-field").click();

    cy.contains(".dropdown-item", "Use sample value").should("contain", "21.4");
  });

  it("only offers to choose automatically once something has been chosen", () => {
    mount(fromFile);
    cy.get(".metadata-field").click();
    cy.get(".dropdown-item").should("not.contain", "Choose automatically");

    mount({ ...fromFile, bound: true });
    cy.get(".metadata-field").click();
    cy.contains(".dropdown-item", "Choose automatically").should("be.visible");
  });

  it("edits in place, starting from the value on show", () => {
    mount(fromFile);
    cy.get(".metadata-field").click();
    cy.contains(".dropdown-item", "Override…").click();

    cy.get("input").should("be.focused").and("have.value", "14.32");
  });

  it("can be backed out of, by the button or by the keyboard", () => {
    mount(fromFile);

    for (const abandon of [
      () => cy.get(".editor .cancel").click(),
      () => cy.get("input").type("{esc}"),
    ]) {
      cy.get(".metadata-field").click();
      cy.contains(".dropdown-item", "Override…").click();
      cy.get("input").clear();
      cy.get("input").type("999");
      abandon();
      cy.get("input").should("not.exist");
      cy.get(".value").should("have.text", "14.32");
    }
  });

  it("still opens on a right-click, for anyone who tries one", () => {
    mount(fromFile);
    cy.get(".value").rightclick();

    cy.contains(".dropdown-item", "Override…").should("be.visible");
  });

  it("does not leave the menu open behind an edit that was saved or abandoned", () => {
    mount(fromFile);
    cy.get(".metadata-field").click();
    cy.contains(".dropdown-item", "Override…").click();
    cy.get(".editor .cancel").click();

    cy.get(".dropdown-menu").should("not.exist");
  });

  it("closes the menu without changing anything", () => {
    mount(fromFile);
    cy.get(".metadata-field").click();
    cy.contains(".dropdown-item", "Cancel").click();

    cy.get(".dropdown-menu").should("not.exist");
    cy.get(".value").should("have.text", "14.32");
  });
});
