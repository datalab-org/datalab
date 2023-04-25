// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import MediaBlock from "@/components/datablocks/MediaBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import ChatBlock from "@/components/datablocks/ChatBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import NMRBlock from "@/components/datablocks/NMRBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";
import CellInformation from "@/components/CellInformation";

import SampleCreateModalAddon from "@/components/itemCreateModalAddons/SampleCreateModalAddon";
import CellCreateModalAddon from "@/components/itemCreateModalAddons/CellCreateModalAddon";

// Look for values set in .env file. Use defaults if `null` is not explicitly handled elsewhere in the code.
export const API_URL =
  process.env.VUE_APP_API_URL != null ? process.env.VUE_APP_API_URL : "http://localhost:5001";
export const API_TOKEN = process.env.VUE_APP_API_TOKEN;

export const LOGO_URL = process.env.VUE_APP_LOGO_URL;
export const HOMEPAGE_URL = process.env.VUE_APP_HOMEPAGE_URL;
export const GRAVATAR_STYLE = "identicon";

export const debounceTime = 250; // time after user stops typing before request is sent

export const blockTypes = {
  generic: { description: "Test Block", component: DataBlockBase },
  comment: { description: "Comment", component: DataBlockBase },
  media: { description: "Media Block", component: MediaBlock },
  xrd: { description: "Powder XRD", component: XRDBlock },
  cycle: { description: "Electrochemistry", component: CycleBlock },
  nmr: { description: "NMR", component: NMRBlock },
  chat: { description: "A. L. L. C. A. P. S.", component: ChatBlock },
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
    isCreateable: false,
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
};

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
