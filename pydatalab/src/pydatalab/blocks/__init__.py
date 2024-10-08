from typing import Dict, Sequence, Type

from pydatalab.apps.buba import BubaBlock

# These app imports will be replaced by dynamic plugins in a future version
from pydatalab.apps.chat.blocks import ChatBlock
from pydatalab.apps.echem import CycleBlock
from pydatalab.apps.eis import EISBlock
from pydatalab.apps.nmr import NMRBlock
from pydatalab.apps.raman import RamanBlock
from pydatalab.apps.tga import MassSpecBlock
from pydatalab.apps.xrd import XRDBlock
from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.common import CommentBlock, MediaBlock, NotSupportedBlock, TabularDataBlock

BLOCKS: Sequence[Type["DataBlock"]] = (
    CommentBlock,
    BubaBlock,
    MediaBlock,
    XRDBlock,
    CycleBlock,
    RamanBlock,
    NMRBlock,
    NotSupportedBlock,
    MassSpecBlock,
    ChatBlock,
    EISBlock,
    TabularDataBlock,
)

BLOCK_TYPES: Dict[str, Type["DataBlock"]] = {block.blocktype: block for block in BLOCKS}

__all__ = (
    "CommentBlock",
    "MediaBlock",
    "XRDBlock",
    "BubaBlock",
    "ChatBlock",
    "EISBlock",
    "CycleBlock",
    "NotSupportedBlock",
    "NMRBlock",
    "RamanBlock",
    "MassSpecBlock",
    "TabularDataBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
