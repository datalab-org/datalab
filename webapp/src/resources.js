// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import ImageBlock from "@/components/datablocks/ImageBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import SynthesisBlock from "@/components/datablocks/SynthesisBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";

export const API_URL = process.env.VUE_APP_API_URL; //"http://localhost:5001";

export const blockTypes = {
  generic: { description: "Test Block", component: DataBlockBase },
  comment: { description: "Comment", component: DataBlockBase },
  image: { description: "Image Block", component: ImageBlock },
  xrd: { description: "Powder XRD", component: XRDBlock },
  cycle: { description: "Electrochemistry", component: CycleBlock },
  synthesis: { description: "Materials Synthesis", component: SynthesisBlock },
};

export const itemTypes = {
  samples: {
    itemInformationComponent: SampleInformation,
    navbarColor: "#0b6093",
    navbarName: "Sample",
  },
  starting_materials: {
    itemInformationComponent: StartingMaterialInformation,
    navbarColor: "#349579",
    navbarName: "Starting Material",
  },
};
