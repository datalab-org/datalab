// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import BokehBlock from "@/components/datablocks/BokehBlock";
import MediaBlock from "@/components/datablocks/MediaBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import ChatBlock from "@/components/datablocks/ChatBlock";
import RamanBlock from "@/components/datablocks/RamanBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import NMRBlock from "@/components/datablocks/NMRBlock";
import EISBlock from "@/components/datablocks/EISBlock";
import MassSpecBlock from "@/components/datablocks/MassSpecBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";
import CellInformation from "@/components/CellInformation";
import CollectionInformation from "@/components/CollectionInformation";
import EquipmentInformation from "@/components/EquipmentInformation";

import SampleCreateModalAddon from "@/components/itemCreateModalAddons/SampleCreateModalAddon";
import CellCreateModalAddon from "@/components/itemCreateModalAddons/CellCreateModalAddon";

// Look for values set in .env file. Use defaults if `null` is not explicitly handled elsewhere in the code.
export const API_URL =
  process.env.VUE_APP_API_URL != null ? process.env.VUE_APP_API_URL : "http://localhost:5001";
export const API_TOKEN = process.env.VUE_APP_API_TOKEN;

export const LOGO_URL = process.env.VUE_APP_LOGO_URL;
export const HOMEPAGE_URL = process.env.VUE_APP_HOMEPAGE_URL;

export const GRAVATAR_STYLE = "identicon";

// determine whether inventory should be readonly (except blocks). Note: environment
// variables can only be strings, not bools.
const editable_inventory = process.env.VUE_APP_EDITABLE_INVENTORY || "false";
export const EDITABLE_INVENTORY = editable_inventory.toLowerCase() == "true";

export const UPPY_MAX_TOTAL_FILE_SIZE =
  Number(process.env.VUE_APP_UPPY_MAX_TOTAL_FILE_SIZE) != null
    ? process.env.VUE_APP_UPPY_MAX_TOTAL_FILE_SIZE
    : 102400000000;
export const UPPY_MAX_NUMBER_OF_FILES =
  Number(process.env.VUE_APP_UPPY_MAX_NUMBER_OF_FILES) != null
    ? process.env.VUE_APP_UPPY_MAX_NUMBER_OF_FILES
    : 10000;

export const debounceTime = 250; // time after user stops typing before request is sent

export const blockTypes = {
  comment: { description: "Comment", component: DataBlockBase, name: "Comment" },
  media: { description: "Media", component: MediaBlock, name: "Media" },
  tabular: { description: "Tabular Data", component: BokehBlock, name: "Tabular data" },
  xrd: { description: "Powder XRD", component: XRDBlock, name: "Powder XRD" },
  raman: { description: "Raman", component: RamanBlock, name: "Raman" },
  cycle: { description: "Electrochemistry", component: CycleBlock, name: "Electrochemistry" },
  eis: { description: "Electrochemical Impedance Spectroscopy", component: EISBlock, name: "EIS" },
  nmr: { description: "Nuclear Magnetic Resonance Spectroscopy", component: NMRBlock, name: "NMR" },
  ms: { description: "Mass Spectrometry", component: MassSpecBlock, name: "Mass Spectrometry" },
  tga_dta: { description: "TGA-DTA", component: BokehBlock, name: "tga-dta" },
  chat: { description: "Virtual assistant", component: ChatBlock, name: "Virtual Assistant" },
};

export const itemTypes = {
  samples: {
    itemInformationComponent: SampleInformation,
    itemCreateModalAddon: SampleCreateModalAddon,
    navbarColor: "#0b6093",
    navbarName: "Sample",
    lightColor: "#d0ebfb",
    labelColor: "#0b6093",
    isCreateable: true,
    display: "sample",
  },
  starting_materials: {
    itemInformationComponent: StartingMaterialInformation,
    navbarColor: "#349579",
    navbarName: "Starting Material",
    lightColor: "#d9f2eb",
    labelColor: "#298651",
    isCreateable: true,
    display: "starting material",
  },
  cells: {
    itemInformationComponent: CellInformation,
    itemCreateModalAddon: CellCreateModalAddon,
    navbarColor: "#946807",
    navbarName: "Cell",
    lightColor: "#D1C28F",
    labelColor: "#946807",
    isCreateable: true,
    display: "cell",
  },
  collections: {
    itemInformationComponent: CollectionInformation,
    navbarColor: "#563D7c",
    navbarName: "Collection",
    lightColor: "#cbd6f7",
    labelColor: "#563D7c",
    display: "collection",
  },
  users: {
    navbarColor: "mediumseagreen",
    navbarName: "User",
    lightColor: "mediumseagreen",
    labelColor: "mediumseagreen",
    isCreateable: false,
    display: "user",
  },
  equipment: {
    itemInformationComponent: EquipmentInformation,
    navbarColor: "#c77c02",
    navbarName: "Equipment",
    lightColor: "#f7d6a1",
    labelColor: "#c77c02",
    display: "equipment",
  },
};

export const SAMPLE_TABLE_TYPES = ["samples", "cells"];
export const INVENTORY_TABLE_TYPES = ["starting_materials"];
export const EQUIPMENT_TABLE_TYPES = ["equipment"];

export const cellFormats = {
  coin: "coin",
  pouch: "pouch",
  in_situ_xrd: "in situ (XRD)",
  in_situ_nmr: "in situ (NMR)",
  in_situ_squid: "in situ (SQUID)",
  swagelok: "swagelok",
  cylindrical: "cylindrical",
  other: "other",
};
