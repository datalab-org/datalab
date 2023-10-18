from typing import Dict, Sequence, Type

# These app imports will be replaced by dynamic plugins in a future version
from pydatalab.apps.chat.blocks import ChatBlock
from pydatalab.apps.echem import CycleBlock
from pydatalab.apps.eis import EISBlock
from pydatalab.apps.mri import MRIBlock
from pydatalab.apps.nmr import NMRBlock
from pydatalab.apps.raman import RamanBlock
from pydatalab.apps.tga import MassSpecBlock
from pydatalab.apps.xrd import XRDBlock
from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.common import CommentBlock, MediaBlock, NotSupportedBlock

BLOCKS: Sequence[Type["DataBlock"]] = (
    CommentBlock,
    MediaBlock,
    XRDBlock,
    CycleBlock,
    RamanBlock,
    MRIBlock,
    NMRBlock,
    MassSpecBlock,
    NotSupportedBlock,
    ChatBlock,
    EISBlock,
)

BLOCK_TYPES: Dict[str, Type["DataBlock"]] = {block.blocktype: block for block in BLOCKS}

__all__ = (
    "CommentBlock",
    "MediaBlock",
    "XRDBlock",
    "ChatBlock",
    "EISBlock",
    "CycleBlock",
    "NMRBlock",
    "RamanBlock",
    "MassSpecBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
