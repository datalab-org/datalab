// Resources for the application
// import DataBlockBase from "@/components/datablocks/DataBlockBase";
// import BokehBlock from "@/components/datablocks/BokehBlock";
// import MediaBlock from "@/components/datablocks/MediaBlock";
// import XRDBlock from "@/components/datablocks/XRDBlock";
// import ChatBlock from "@/components/datablocks/ChatBlock";
// import RamanBlock from "@/components/datablocks/RamanBlock";
// import CycleBlock from "@/components/datablocks/CycleBlock";
// import NMRBlock from "@/components/datablocks/NMRBlock";
// import EISBlock from "@/components/datablocks/EISBlock";
// import MassSpecBlock from "@/components/datablocks/MassSpecBlock";
import DataBlockUI from "@/components/DataBlockUI";
import NMRInsituBlock from "@/components/datablocks/NMRInsituBlock";

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

export const QR_CODE_RESOLVER_URL = process.env.VUE_APP_QR_CODE_RESOLVER_URL;

export const FEDERATION_QR_CODE_RESOLVER_URL = "https://purl.datalab-org.io";

export const LOGO_URL = process.env.VUE_APP_LOGO_URL;
export const HOMEPAGE_URL = process.env.VUE_APP_HOMEPAGE_URL;
export const APP_VERSION = process.env.VUE_APP_GIT_VERSION;

export const GRAVATAR_STYLE = "identicon";

// determine whether inventory should be readonly (except blocks). Note: environment
// variables can only be strings, not bools.
const editable_inventory = process.env.VUE_APP_EDITABLE_INVENTORY || "false";
export const EDITABLE_INVENTORY = editable_inventory.toLowerCase() == "true";

const automatically_generate_id_default =
  process.env.VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT || "false";
export const AUTOMATICALLY_GENERATE_ID_DEFAULT =
  automatically_generate_id_default.toLowerCase() == "true";

// Eventually this should be pulled from the schema
export const DATETIME_FIELDS = new Set(["date"]);

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
  comment: {
    description: "Comment",
    component: DataBlockUI,
    name: "Comment",
    properties: {},
  },
  media: {
    description: "Media",
    component: DataBlockUI,
    name: "Media",
    properties: {
      mediaDisplay: { type: "media" },
    },
  },
  tabular: {
    description: "Tabular Data",
    component: DataBlockUI,
    name: "Tabular data",
    properties: {
      bokehPlot: { type: "plot" },
    },
  },
  xrd: {
    description: "Powder XRD",
    component: DataBlockUI,
    name: "Powder XRD",
    properties: {
      bokehPlot: { type: "plot" },
      wavelength: {
        type: "float",
        label: "Wavelength (Å):",
        default: 1.54,
      },
    },
  },
  raman: {
    description: "Raman",
    component: DataBlockUI,
    name: "Raman",
    properties: {
      bokehPlot: { type: "plot" },
    },
  },
  cycle: {
    description: "Electrochemistry",
    component: DataBlockUI,
    name: "Electrochemistry",
    properties: {
      bokehPlot: { type: "plot" },
      cycle: {
        type: "string",
        label: "Cycles to plot:",
        placeholder: "e.g., 1-5, 7, 9-10. Starts at 1.",
      },
      derivativeMode: {
        type: "selector",
        options: [
          { value: "final capacity", label: "Cycle Summary" },
          { value: "dQ/dV", label: "dQ/dV" },
          { value: "dV/dQ", label: "dV/dQ" },
        ],
      },
      s_spline: {
        type: "slider",
        min: 1,
        max: 10,
        step: 0.2,
        label: "Spline fit:",
        description:
          "Smoothing parameter that determines how close the spline fits to the real data. Larger values result in a smoother fit with decreased detail.",
      },
      win_size_1: {
        type: "slider",
        min: 501,
        max: 1501,
        step: 1,
        label: "Window Size 1:",
        description: "Window size for the Savitzky-Golay filter to apply to the derivatives.",
      },
    },
  },
  eis: {
    description: "Electrochemical Impedance Spectroscopy",
    component: DataBlockUI,
    name: "EIS",
    properties: {
      bokehPlot: { type: "plot" },
    },
  },
  nmr: {
    description: "Nuclear Magnetic Resonance Spectroscopy",
    component: DataBlockUI,
    name: "NMR",
    properties: {
      bokehPlot: { type: "plot" },
      processNumber: {
        type: "select",
        label: "Process number:",
        optionsFrom: "available_processes",
      },
      details: {
        type: "toggleDetails",
        toggles: [
          { key: "titleShown", label: "show title", hideLabel: "hide title" },
          {
            key: "detailsShown",
            label: "show measurement details",
            hideLabel: "hide measurement details",
          },
        ],
      },
    },
  },
  ms: {
    description: "Mass Spectrometry",
    component: DataBlockUI,
    name: "Mass Spectrometry",
    properties: {
      bokehPlot: { type: "plot" },
    },
  },
  chat: {
    description: "Virtual assistant",
    component: DataBlockUI,
    name: "Virtual Assistant",
    properties: {
      chat: {
        type: "chat",
        advanced: {
          modelSelector: true,
          tokenCount: true,
          costEstimation: true,
          temperature: {
            min: 0,
            max: 1,
            step: 0.1,
          },
        },
      },
    },
  },
  ftir: {
    description: "FTIR",
    component: DataBlockUI,
    name: "FTIR",
    properties: {
      bokehPlot: { type: "plot" },
    },
  },
  "insitu-nmr": { description: "NMR insitu", component: NMRInsituBlock, name: "NMR insitu" },
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
  in_situ_optical: "in situ (optical)",
  swagelok: "swagelok",
  cylindrical: "cylindrical",
  other: "other",
};

export const HazardPictograms = {
  GHS01: {
    code: "GHS01",
    label: "Explosives",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS01.svg",
  },
  GHS02: {
    code: "GHS02",
    label: "Flammables",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS02.svg",
  },
  GHS03: {
    code: "GHS03",
    label: "Oxidizers",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS03.svg",
  },
  GHS04: {
    code: "GHS04",
    label: "Compressed Gases",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS04.svg",
  },
  GHS05: {
    code: "GHS05",
    label: "Corrosives",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS05.svg",
  },
  GHS06: {
    code: "GHS06",
    label: "Acute Toxicity",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS06.svg",
  },
  GHS07: {
    code: "GHS07",
    label: "Irritant",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS07.svg",
  },
  GHS08: {
    code: "GHS08",
    label: "Health Hazard",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS08.svg",
  },
  GHS09: {
    code: "GHS09",
    label: "Environment",
    pictogram: "https://pubchem.ncbi.nlm.nih.gov/images/ghs/GHS09.svg",
  },
};

export function getHCodesFromHazardStatement(hazardStatement) {
  const hazardCodeRegex = /H\d{3}/g;
  return hazardStatement.match(hazardCodeRegex) || [];
}

export function getPictogramsFromHazardInformation(hazardInformation) {
  const hCodes = getHCodesFromHazardStatement(hazardInformation);

  let pictograms = new Set([]);
  hCodes.forEach((code) => {
    const numericCode = Number(code.replace("H", ""));
    pictograms = pictograms.union(getPictogramsFromHazardCode(numericCode));
  });

  return pictograms;
}

export function getPictogramsFromHazardCode(code) {
  let pictograms = new Set([]);
  if (
    (code >= 200 && code <= 204) ||
    (code >= 209 && code <= 211) ||
    (code >= 240 && code <= 241)
  ) {
    pictograms.add(HazardPictograms.GHS01);
  }

  if (
    (code >= 205 && code <= 208) ||
    (code >= 220 && code <= 226) ||
    (code >= 228 && code <= 232) ||
    (code >= 241 && code <= 242) ||
    (code >= 250 && code <= 252) ||
    (code >= 260 && code <= 261) ||
    (code >= 282 && code <= 283)
  ) {
    pictograms.add(HazardPictograms.GHS02);
  }

  if (code >= 270 && code <= 272) {
    pictograms.add(HazardPictograms.GHS03);
  }
  if (code >= 280 && code <= 284) {
    pictograms.add(HazardPictograms.GHS04);
  }
  if (code === 290 || code === 314 || code === 318) {
    pictograms.add(HazardPictograms.GHS05);
  }
  if (
    (code >= 300 && code <= 301) ||
    (code >= 310 && code <= 311) ||
    (code >= 330 && code <= 331)
  ) {
    pictograms.add(HazardPictograms.GHS06);
  }
  if (
    code === 204 ||
    code === 302 ||
    code === 312 ||
    code === 315 ||
    code === 317 ||
    code === 319 ||
    code === 332 ||
    (code >= 335 && code <= 336) ||
    code === 420
  ) {
    pictograms.add(HazardPictograms.GHS07);
  }
  if (
    (code >= 304 && code <= 305) ||
    (code >= 2 && code <= 2) ||
    code === 334 ||
    (code >= 340 && code <= 341) ||
    (code >= 350 && code <= 351) ||
    (code >= 360 && code <= 361) ||
    (code >= 370 && code <= 373)
  ) {
    pictograms.add(HazardPictograms.GHS08);
  }
  if (code === 400 || (code >= 410 && code <= 411)) {
    pictograms.add(HazardPictograms.GHS09);
  }
  return pictograms;
}
