// Resources for the application
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import ImageBlock from "@/components/datablocks/ImageBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
// import SynthesisBlock from "@/components/datablocks/SynthesisBlock"
// note: SynthesisBlock not yet implemented

export const API_URL = "http://localhost:5001";

export const blockKinds = {
  generic: { description: "Test Block", component: DataBlockBase },
  comment: { description: "Comment", component: DataBlockBase },
  image: { description: "Image Block", component: ImageBlock },
  xrd: { description: "Powder XRD", component: XRDBlock },
  cycle: { description: "Electrochemistry", component: CycleBlock },
  //synthesis: { description: "Materials Synthesis", component:SynthesisBlock },
};
