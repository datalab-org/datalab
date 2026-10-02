// This file was edited with the assistance of an AI model and requires human review from the contributor.
import { createStore } from "vuex";

import CreateItemModal from "@/components/CreateItemModal.vue";
import CustomFieldsPanel from "@/components/custom/CustomFieldsPanel.vue";
import { itemTypes, registerDynamicItemType } from "@/resources.js";

const DIRECT_TYPE = "_component_test_direct_item";
const EQUIPMENT_TYPE = "_component_test_equipment_item";

describe("Custom item UI", () => {
  afterEach(() => {
    delete itemTypes[DIRECT_TYPE];
    delete itemTypes[EQUIPMENT_TYPE];
  });

  it("offers every dynamic type from Samples but not Inventory", () => {
    registerDynamicItemType(DIRECT_TYPE, {
      title: "Direct item",
      base_type: "items",
    });
    registerDynamicItemType(EQUIPMENT_TYPE, {
      title: "Custom equipment",
      base_type: "equipment",
    });

    const schemas = { [DIRECT_TYPE]: {}, [EQUIPMENT_TYPE]: {} };
    const samplesTypes = CreateItemModal.computed.effectiveAllowedTypes.call({
      allowedTypes: ["samples", "cells"],
      $store: { state: { schemas } },
    });
    const inventoryTypes = CreateItemModal.computed.effectiveAllowedTypes.call({
      allowedTypes: ["starting_materials"],
      $store: { state: { schemas } },
    });

    expect(samplesTypes).to.deep.equal(["samples", "cells", DIRECT_TYPE, EQUIPMENT_TYPE]);
    expect(inventoryTypes).to.deep.equal(["starting_materials"]);
    expect(itemTypes[DIRECT_TYPE].itemInformationComponent.name).to.equal("ItemInformation");
  });

  it("renders only fields added beyond the advertised Item base", () => {
    registerDynamicItemType(DIRECT_TYPE, {
      title: "Direct item",
      base_type: "items",
    });

    const store = createStore({
      state() {
        return {
          all_item_data: {
            direct1: {
              item_id: "direct1",
              type: DIRECT_TYPE,
              name: "Inherited name",
              width: 12,
              height: 4,
            },
          },
          schemas: {
            [DIRECT_TYPE]: {
              attributes: {
                base_type: "items",
                base_fields: ["item_id", "type", "name"],
                schema: {
                  title: "Direct item",
                  type: "object",
                  properties: {
                    item_id: { title: "Item ID", type: "string" },
                    type: { title: "Type", type: "string" },
                    name: { title: "Name", type: "string" },
                    width: { title: "Width", type: "number" },
                    height: { title: "Height", type: "number" },
                  },
                },
              },
            },
          },
        };
      },
      mutations: {
        updateItemData(state, { item_id, item_data }) {
          Object.assign(state.all_item_data[item_id], item_data);
        },
      },
    });

    cy.mount(CustomFieldsPanel, {
      props: { item_id: "direct1", itemType: DIRECT_TYPE },
      global: { plugins: [store] },
    });

    cy.findByLabelText("Width").should("have.value", "12");
    cy.findByLabelText("Height").should("have.value", "4");
    cy.findByLabelText("Name").should("not.exist");
    cy.findByLabelText("Item ID").should("not.exist");
  });

  it("asks whether to convert a populated value when its unit changes", () => {
    registerDynamicItemType(DIRECT_TYPE, {
      title: "Direct item",
      base_type: "items",
    });

    const store = createStore({
      state() {
        return {
          all_item_data: {
            direct1: {
              item_id: "direct1",
              type: DIRECT_TYPE,
              voltage: 1,
              voltage_display_unit: "V",
            },
          },
          schemas: {
            [DIRECT_TYPE]: {
              attributes: {
                base_fields: ["item_id", "type"],
                schema: {
                  type: "object",
                  properties: {
                    item_id: { type: "string" },
                    type: { type: "string" },
                    voltage: {
                      title: "Voltage",
                      type: "number",
                      datalab_quantity: {
                        canonical_unit: "V",
                        default_display_unit: "V",
                        display_unit_field: "voltage_display_unit",
                        display_units: {
                          V: { scale: 1, offset: 0 },
                          mV: { scale: 0.001, offset: 0 },
                        },
                      },
                    },
                    voltage_display_unit: { type: "string", enum: ["V", "mV"] },
                  },
                },
              },
            },
          },
        };
      },
      mutations: {
        updateItemData(state, { item_id, item_data }) {
          Object.assign(state.all_item_data[item_id], item_data);
        },
      },
    });

    cy.mount(CustomFieldsPanel, {
      props: { item_id: "direct1", itemType: DIRECT_TYPE },
      global: { plugins: [store] },
    });

    cy.get(".unit-select").select("mV");
    cy.contains("Convert value:").should("be.visible");
    cy.contains("1000 mV").should("be.visible");
    cy.findByRole("button", { name: "Convert value" }).click();
    cy.findByLabelText("Voltage").should("have.value", "1000");
    cy.then(() => expect(store.state.all_item_data.direct1.voltage).to.equal(1));

    cy.get(".unit-select").select("V");
    cy.findByRole("button", { name: "Keep number" }).click();
    cy.findByLabelText("Voltage").should("have.value", "1000");
    cy.then(() => expect(store.state.all_item_data.direct1.voltage).to.equal(1000));
  });

  it("converts quantities without storing a display unit", () => {
    registerDynamicItemType(DIRECT_TYPE, {
      title: "Direct item",
      base_type: "items",
    });

    const store = createStore({
      state() {
        return {
          all_item_data: {
            direct1: { item_id: "direct1", type: DIRECT_TYPE, mass: 1500, molar_mass: 55.8 },
          },
          schemas: {
            [DIRECT_TYPE]: {
              attributes: {
                base_fields: ["item_id", "type"],
                schema: {
                  type: "object",
                  properties: {
                    item_id: { type: "string" },
                    type: { type: "string" },
                    // No `display_unit_field`: the chosen unit is not stored with the item.
                    mass: {
                      title: "Mass",
                      type: "number",
                      datalab_quantity: {
                        canonical_unit: "mg",
                        display_units: { mg: { scale: 1 }, g: { scale: 1000 } },
                      },
                    },
                    // No `display_units` either: only ever shown in the canonical unit.
                    molar_mass: {
                      title: "Molar mass",
                      type: "number",
                      datalab_quantity: { canonical_unit: "g/mol" },
                    },
                  },
                },
              },
            },
          },
        };
      },
      mutations: {
        updateItemData(state, { item_id, item_data }) {
          Object.assign(state.all_item_data[item_id], item_data);
        },
      },
    });

    cy.mount(CustomFieldsPanel, {
      props: { item_id: "direct1", itemType: DIRECT_TYPE },
      global: { plugins: [store] },
    });

    // A canonical-only quantity shows its unit as a plain label, with no selector.
    cy.findByLabelText("Molar mass").should("have.value", "55.8");
    cy.contains(".input-group-text", "g/mol").should("be.visible");
    cy.get(".unit-select").should("have.length", 1);

    cy.findByLabelText("Mass").should("have.value", "1500");
    cy.get(".unit-select").select("g");
    cy.findByRole("button", { name: "Convert value" }).click();
    cy.findByLabelText("Mass").should("have.value", "1.5");

    // Values entered in the display unit are stored in the canonical unit, and only
    // the canonical value is written to the item.
    cy.findByLabelText("Mass").clear().type("2").blur();
    cy.then(() => {
      expect(store.state.all_item_data.direct1).to.deep.equal({
        item_id: "direct1",
        type: DIRECT_TYPE,
        mass: 2000,
        molar_mass: 55.8,
      });
    });
  });
});
