// This file was edited with the assistance of an AI model and requires human review from the contributor.
import CellInformation from "@/components/CellInformation.vue";
import store from "@/store/index.js";

// The quantity hints as served in the cell schema: every value is stored in its
// canonical unit, and only `nominal_capacity` persists the unit it is displayed in.
const CELL_SCHEMA = {
  type: "object",
  properties: {
    characteristic_mass: {
      type: "number",
      datalab_quantity: {
        canonical_unit: "mg",
        display_units: { mg: { scale: 1 }, g: { scale: 1000 } },
      },
    },
    characteristic_molar_mass: { type: "number", datalab_quantity: { canonical_unit: "g/mol" } },
    theoretical_capacity: { type: "number", datalab_quantity: { canonical_unit: "mAh/g" } },
    nominal_capacity: {
      type: "number",
      datalab_quantity: {
        canonical_unit: "mAh",
        default_display_unit: "mAh",
        display_unit_field: "nominal_capacity_unit",
        display_units: { mAh: { scale: 1 }, Ah: { scale: 1000 } },
      },
    },
    nominal_capacity_unit: { type: "string", enum: ["mAh", "Ah"] },
  },
};

// The form's field helpers read and write the application store directly, so the
// component is mounted against it rather than a stand-in.
function mountCell(item) {
  store.commit("setSchema", { type: "cells", schema: { attributes: { schema: CELL_SCHEMA } } });
  store.commit("createItemData", {
    item_id: "cell1",
    refcode: "test:CELL01",
    item_data: { item_id: "cell1", type: "cells", ...item },
    child_items: [],
    parent_items: [],
  });

  cy.intercept("**/locations*", { status: "success", locations: [] });
  cy.mount(CellInformation, {
    props: { item_id: "cell1" },
    global: {
      plugins: [store],
      stubs: {
        ChemFormulaInput: true,
        TiptapInline: true,
        CellPreparationInformation: true,
        TableOfContents: true,
        ItemRelationshipVisualization: true,
        FormattedRefcode: true,
        ToggleableCollectionFormGroup: true,
        ToggleableCreatorsFormGroup: true,
        ToggleableItemStatusFormGroup: true,
        ToggleableGroupsFormGroup: true,
        ToggleableTagsFormGroup: true,
        LocationInput: true,
      },
    },
  });
  return store;
}

describe("Cell quantities", () => {
  it("labels fields with the units declared in the schema", () => {
    mountCell({});
    cy.contains("label", "Theoretical capacity (mAh/g)").should("exist");
    cy.contains("label", "Molar mass (g/mol)").should("exist");
    cy.get("#cell-characteristic-mass-unit").should("have.value", "mg");
    cy.get("#cell-nominal-capacity-unit").should("have.value", "mAh");
  });

  it("converts the active mass for display without storing the unit", () => {
    const store = mountCell({ characteristic_mass: 5 });
    const cell = () => store.state.all_item_data.cell1;

    cy.get("#cell-characteristic-mass").should("have.value", "5");
    cy.get("#cell-characteristic-mass-unit").select("g");
    cy.get("#cell-characteristic-mass").should("have.value", "0.005");
    cy.then(() => {
      expect(cell()).to.deep.equal({ item_id: "cell1", type: "cells", characteristic_mass: 5 });
    });

    cy.get("#cell-characteristic-mass").clear().type("0.01");
    cy.then(() => expect(cell().characteristic_mass).to.equal(10));
  });

  it("calculates the nominal capacity until a different value is provided", () => {
    const store = mountCell({ characteristic_mass: 5, theoretical_capacity: 200 });
    const cell = () => store.state.all_item_data.cell1;

    // Unset: the calculated value (200 mAh/g * 5 mg) is shown but not written to the item.
    cy.get("#cell-nominal-capacity").should("have.value", "1");
    cy.contains("reset to calculated").should("not.exist");
    cy.contains("Doesn't match").should("not.exist");
    cy.then(() => expect(cell().nominal_capacity).to.equal(undefined));

    // A provided value is stored in mAh whichever unit it is entered in, and is flagged
    // as an override because it differs from the calculation.
    cy.get("#cell-nominal-capacity-unit").select("Ah");
    cy.get("#cell-nominal-capacity").should("have.value", "0.001");
    cy.get("#cell-nominal-capacity").clear().type("0.005");
    cy.then(() => {
      expect(cell().nominal_capacity).to.equal(5);
      expect(cell().nominal_capacity_unit).to.equal("Ah");
    });
    cy.contains("Doesn't match").should("contain", "0.001 Ah");

    // An override is left alone when the calculation changes...
    cy.get("#cell-characteristic-mass").clear().type("10");
    cy.then(() => expect(cell().nominal_capacity).to.equal(5));

    // ...until it is reset.
    cy.contains("reset to calculated").click();
    cy.then(() => expect(cell().nominal_capacity).to.equal(null));
    cy.get("#cell-nominal-capacity").should("have.value", "0.002");
    cy.contains("Doesn't match").should("not.exist");
  });

  it("unsets a stored value that was following the calculation when it changes", () => {
    mountCell({
      characteristic_mass: 5,
      theoretical_capacity: 200,
      nominal_capacity: 1,
      nominal_capacity_unit: "mAh",
    });

    // The stored value matches the calculation, so it is not an override...
    cy.get("#cell-nominal-capacity").should("have.value", "1");
    cy.contains("reset to calculated").should("not.exist");

    // ...and is unset when the calculation changes, leaving the server to recompute
    // it on save rather than keeping a stale value that would read as an override.
    cy.get("#cell-characteristic-mass").clear().type("10");
    cy.get("#cell-nominal-capacity").should("have.value", "2");
    cy.then(() => expect(store.state.all_item_data.cell1.nominal_capacity).to.equal(null));
    cy.contains("Doesn't match").should("not.exist");
  });
});
