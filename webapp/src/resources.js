// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import ImageBlock from "@/components/datablocks/ImageBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import NMRBlock from "@/components/datablocks/NMRBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";

// Look for values set in .env file. Use defaults if `null` is not explicitly handled elsewhere in the code.
export const API_URL =
  process.env.VUE_APP_API_URL != null ? process.env.VUE_APP_API_URL : "http://localhost:5001";
export const API_TOKEN = process.env.VUE_APP_API_TOKEN;

export const debounceTime = 250; // time after user stops typing before request is sent

export const blockTypes = {
  generic: { description: "Test Block", component: DataBlockBase },
  comment: { description: "Comment", component: DataBlockBase },
  image: { description: "Image Block", component: ImageBlock },
  xrd: { description: "Powder XRD", component: XRDBlock },
  cycle: { description: "Electrochemistry", component: CycleBlock },
  nmr: { description: "NMR", component: NMRBlock },
};

export const itemTypes = {
  samples: {
    itemInformationComponent: SampleInformation,
    navbarColor: "#0b6093",
    navbarName: "Sample",
    lightColor: "#d0ebfb",
    labelColor: "#0b6093",
  },
  starting_materials: {
    itemInformationComponent: StartingMaterialInformation,
    navbarColor: "#349579",
    navbarName: "Starting Material",
    lightColor: "#d9f2eb",
    labelColor: "#298651",
  },
};
