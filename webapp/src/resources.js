// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import ImageBlock from "@/components/datablocks/ImageBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
// import SynthesisBlock from "@/components/datablocks/SynthesisBlock";

import SampleInformation from "@/components/SampleInformation";
import StartingMaterialInformation from "@/components/StartingMaterialInformation";

export const API_URL = process.env.VUE_APP_API_URL; //"http://localhost:5001";

export const blockKinds = {
  generic: { description: "Test Block", component: DataBlockBase },
  comment: { description: "Comment", component: DataBlockBase },
  image: { description: "Image Block", component: ImageBlock },
  xrd: { description: "Powder XRD", component: XRDBlock },
  cycle: { description: "Electrochemistry", component: CycleBlock },
  // synthesis: { description: "Materials Synthesis", component: SynthesisBlock },
};

export const itemTypes = {
  samples: { itemInformationComponent: SampleInformation },
  starting_materials: { itemInformationComponent: StartingMaterialInformation },
};
