import CreateItemModal from "@/components/CreateItemModal.vue";
import CreateEquipmentModal from "@/components/CreateEquipmentModal.vue";
import {
  itemTypes,
  registerDynamicItemType,
  expandItemTypes,
  INVENTORY_TABLE_TYPES,
  EQUIPMENT_TABLE_TYPES,
  INVENTORY_TYPES,
} from "@/resources.js";

const SM_TYPE = "_test_hinted_starting_material";
const EQ_TYPE = "_test_hinted_equipment";
const PLAIN_TYPE = "_test_plain_starting_material";

describe("Custom item types with datalab_behave_as", () => {
  afterEach(() => {
    for (const type of [SM_TYPE, EQ_TYPE, PLAIN_TYPE]) {
      delete itemTypes[type];
      for (const list of [INVENTORY_TABLE_TYPES, EQUIPMENT_TABLE_TYPES, INVENTORY_TYPES]) {
        if (list.includes(type)) list.splice(list.indexOf(type), 1);
      }
    }
  });

  it("lists, creates and searches hinted types with their built-in type", () => {
    registerDynamicItemType(SM_TYPE, { behave_as: "starting_materials" });
    registerDynamicItemType(EQ_TYPE, { behave_as: "equipment" });
    registerDynamicItemType(PLAIN_TYPE, {});

    const schemas = { [SM_TYPE]: {}, [EQ_TYPE]: {}, [PLAIN_TYPE]: {} };
    const allowedTypes = (types) =>
      CreateItemModal.computed.effectiveAllowedTypes.call({
        allowedTypes: types,
        $store: { state: { schemas } },
      });

    expect(allowedTypes(["samples", "cells"])).to.deep.equal(["samples", "cells", PLAIN_TYPE]);
    expect(allowedTypes(INVENTORY_TABLE_TYPES)).to.deep.equal(["starting_materials", SM_TYPE]);
    expect(Object.keys(CreateEquipmentModal.computed.availableTypes.call({}))).to.deep.equal([
      "equipment",
      EQ_TYPE,
    ]);
    expect(INVENTORY_TYPES).to.include.members([SM_TYPE, EQ_TYPE]).and.not.include(PLAIN_TYPE);
    expect(expandItemTypes(["samples", "starting_materials"])).to.deep.equal([
      "samples",
      "starting_materials",
      SM_TYPE,
    ]);
  });
});
