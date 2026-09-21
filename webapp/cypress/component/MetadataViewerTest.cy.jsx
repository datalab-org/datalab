import MetadataViewer from "@/components/MetadataViewer.vue";

describe("MetadataViewer", () => {
  const fields = (mass) => ({
    sample_mass_mg: {
      value: mass,
      source: mass === null ? "user" : "file",
      bound: mass === null,
      available: {},
    },
    molar_mass_g_mol: { value: 192.7, source: "sample", bound: false, available: {} },
    comment: { value: "eicosane", source: "file", bound: false, available: {} },
  });

  const labels = () =>
    cy.get(".metadata-list dt").then(($dt) => [...$dt].map((el) => el.textContent.trim()));

  it("keeps a field in its place when it is emptied", () => {
    // The order a block declares its metadata in, not the order of whatever
    // happens to have a value: a field that moves when you clear it, and moves
    // back when you fill it in, is impossible to work with.
    cy.mount(MetadataViewer, {
      propsData: {
        metadata: { sample_mass_mg: 14.32, molar_mass_g_mol: 192.7, comment: "eicosane" },
        fields: fields(14.32),
        item_id: "i",
        block_id: "b",
      },
    });
    labels().should("deep.equal", ["Sample mass mg", "Molar mass g mol", "Comment"]);

    // The server drops empty values from `metadata` entirely, so this is what
    // arrives once the mass is cleared.
    cy.mount(MetadataViewer, {
      propsData: {
        metadata: { molar_mass_g_mol: 192.7, comment: "eicosane" },
        fields: fields(null),
        item_id: "i",
        block_id: "b",
      },
    });
    labels().should("deep.equal", ["Sample mass mg", "Molar mass g mol", "Comment"]);
  });

  it("still leaves out an empty value nothing is tracking", () => {
    cy.mount(MetadataViewer, {
      propsData: { metadata: { kept: 1, dropped: null } },
    });

    labels().should("deep.equal", ["Kept"]);
  });
});
