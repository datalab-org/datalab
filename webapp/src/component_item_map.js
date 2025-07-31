import DataBlockBase from "@/components/datablocks/DataBlockBase";
import MediaBlock from "@/components/datablocks/MediaBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import ChatBlock from "@/components/datablocks/ChatBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import NMRBlock from "@/components/datablocks/NMRBlock";
import NMRInsituBlock from "@/components/datablocks/NMRInsituBlock";
import UVVisInsituBlock from "@/components/datablocks/UVVisInsituBlock.vue";
import UVVisBlock from "@/components/datablocks/UVVisBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";
import CellInformation from "@/components/CellInformation";
import CollectionInformation from "@/components/CollectionInformation";
import EquipmentInformation from "@/components/EquipmentInformation";

import SampleCreateModalAddon from "@/components/itemCreateModalAddons/SampleCreateModalAddon";
import CellCreateModalAddon from "@/components/itemCreateModalAddons/CellCreateModalAddon";
import StartingMaterialCreateModalAddon from "./components/itemCreateModalAddons/StartingMaterialCreateModalAddon.vue";

// A mapping for blocks that need custom Vue components
export const customBlockTypes = {
  comment: { description: "Comment", component: DataBlockBase, name: "Comment" },
  media: { description: "Media", component: MediaBlock, name: "Media" },
  xrd: { description: "Powder XRD", component: XRDBlock, name: "Powder XRD" },
  cycle: { description: "Electrochemistry", component: CycleBlock, name: "Electrochemistry" },
  nmr: { description: "Nuclear Magnetic Resonance Spectroscopy", component: NMRBlock, name: "NMR" },
  chat: { description: "Virtual assistant", component: ChatBlock, name: "Virtual Assistant" },
  "uv-vis": { description: "UV-Vis", component: UVVisBlock, name: "UV-Vis" },
  "insitu-nmr": { description: "NMR insitu", component: NMRInsituBlock, name: "NMR insitu" },
  "insitu-uvvis": {
    description: "UV-Vis insitu",
    component: UVVisInsituBlock,
    name: "UV-Vis insitu",
  },
};

export const itemTypeComponents = {
  samples: {
    itemInformationComponent: SampleInformation,
    itemCreateModalAddon: SampleCreateModalAddon,
  },
  starting_materials: {
    itemInformationComponent: StartingMaterialInformation,
    itemCreateModalAddon: StartingMaterialCreateModalAddon,
  },
  cells: {
    itemInformationComponent: CellInformation,
    itemCreateModalAddon: CellCreateModalAddon,
  },
  collections: {
    itemInformationComponent: CollectionInformation,
  },
  users: {},
  equipment: {
    itemInformationComponent: EquipmentInformation,
  },
};
