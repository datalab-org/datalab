import { getBlockTypes } from "@/server_fetch_utils.js";
import store from "@/store/index.js";
import GenericBlock from "@/components/datablocks/GenericBlock";
import TemplatedBokehBlock from "@/components/datablocks/TemplatedBokehBlock";
import MediaBlock from "@/components/datablocks/MediaBlock";
import XRDBlock from "@/components/datablocks/XRDBlock";
import ChatBlock from "@/components/datablocks/ChatBlock";
import RamanBlock from "@/components/datablocks/RamanBlock";
import CycleBlock from "@/components/datablocks/CycleBlock";
import NMRBlock from "@/components/datablocks/NMRBlock";
import EISBlock from "@/components/datablocks/EISBlock";
import MassSpecBlock from "@/components/datablocks/MassSpecBlock";

if (store.state.block_types.length == 0) {
  getBlockTypes();
}
let serverBlockTypes = store.state.block_types;

let blockTypeComponentMap = {
  generic: GenericBlock,
  comment: GenericBlock,
  media: MediaBlock,
  xrd: XRDBlock,
  raman: RamanBlock,
  cycle: CycleBlock,
  eis: EISBlock,
  nmr: NMRBlock,
  ms: MassSpecBlock,
  chat: ChatBlock,
};

for (const b in serverBlockTypes) {
  if (b.id in blockTypeComponentMap) {
    continue;
  } else {
    blockTypeComponentMap[b.id] = GenericBlock;
  }
}

export const blockTypes = blockTypeComponentMap;
