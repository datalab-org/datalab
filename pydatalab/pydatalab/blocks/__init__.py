from typing import Dict, Sequence, Type

from pydatalab.apps.chat.blocks import ChatBlock
from pydatalab.apps.eis import EISBlock
from pydatalab.blocks.blocks import (
    CommentBlock,
    DataBlock,
    MediaBlock,
    NMRBlock,
    NotSupportedBlock,
    XRDBlock,
)
from pydatalab.blocks.echem_block import CycleBlock
from pydatalab.blocks.tga_block import TGABlock

BLOCKS: Sequence[Type[DataBlock]] = (
    DataBlock,
    CommentBlock,
    MediaBlock,
    XRDBlock,
    CycleBlock,
    NMRBlock,
    TGABlock,
    NotSupportedBlock,
    ChatBlock,
    EISBlock,
)

BLOCK_TYPES: Dict[str, Type[DataBlock]] = {block.blocktype: block for block in BLOCKS}
BLOCK_TYPES["test"] = DataBlock

__all__ = (
    "DataBlock",
    "CommentBlock",
    "MediaBlock",
    "XRDBlock",
    "ChatBlock",
    "EISBlock",
    "CycleBlock",
    "NMRBlock",
    "TGABlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
