// Look for values set in .env file. Use defaults if `null` is not explicitly handled elsewhere in the code.
export const API_URL =
  import.meta.env.VITE_APP_API_URL != null
    ? import.meta.env.VITE_APP_API_URL
    : "http://localhost:5001";
export const API_TOKEN = import.meta.env.VITE_APP_API_TOKEN;

export const QR_CODE_RESOLVER_URL = import.meta.env.VITE_APP_QR_CODE_RESOLVER_URL;

export const FEDERATION_QR_CODE_RESOLVER_URL = "https://purl.datalab-org.io";

export const LOGO_URL = import.meta.env.VITE_APP_LOGO_URL;
export const HOMEPAGE_URL = import.meta.env.VITE_APP_HOMEPAGE_URL;
export const APP_VERSION = import.meta.env.VITE_APP_GIT_VERSION;

export const GRAVATAR_STYLE = "identicon";

// determine whether inventory should be readonly (except blocks). Note: environment
// variables can only be strings, not bools.
const editable_inventory = import.meta.env.VITE_APP_EDITABLE_INVENTORY || "false";
export const EDITABLE_INVENTORY = editable_inventory.toLowerCase() == "true";

const automatically_generate_id_default =
  import.meta.env.VITE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT || "false";
export const AUTOMATICALLY_GENERATE_ID_DEFAULT =
  automatically_generate_id_default.toLowerCase() == "true";

// Eventually this should be pulled from the schema
export const DATETIME_FIELDS = new Set(["date"]);

export const UPPY_MAX_TOTAL_FILE_SIZE =
  Number(import.meta.env.VITE_APP_UPPY_MAX_TOTAL_FILE_SIZE) != null
    ? import.meta.env.VITE_APP_UPPY_MAX_TOTAL_FILE_SIZE
    : 102400000000;
export const UPPY_MAX_NUMBER_OF_FILES =
  Number(import.meta.env.VITE_APP_UPPY_MAX_NUMBER_OF_FILES) != null
    ? import.meta.env.VITE_APP_UPPY_MAX_NUMBER_OF_FILES
    : 10000;

export const debounceTime = 250; // time after user stops typing before request is sent

export const itemTypes = {
  samples: {
    navbarColor: "#0b6093",
    navbarName: "Sample",
    lightColor: "#d0ebfb",
    labelColor: "#0b6093",
    isCreateable: true,
    display: "sample",
  },
  starting_materials: {
    navbarColor: "#349579",
    navbarName: "Starting Material",
    lightColor: "#d9f2eb",
    labelColor: "#298651",
    isCreateable: true,
    display: "starting material",
  },
  cells: {
    navbarColor: "#946807",
    navbarName: "Cell",
    lightColor: "#D1C28F",
    labelColor: "#946807",
    isCreateable: true,
    display: "cell",
  },
  collections: {
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
