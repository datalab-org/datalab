from typing import Dict, Sequence, Type

from pydatalab.apps.chat.blocks import ChatBlock
from pydatalab.apps.eis import EISBlock
from pydatalab.apps.tga import MassSpecBlock

from pydatalab.blocks.blocks import (
    CommentBlock,
    DataBlock,
    MediaBlock,
    NMRBlock,
    NotSupportedBlock,
    XRDBlock,
)
from pydatalab.blocks.echem_block import CycleBlock

BLOCKS: Sequence[Type[DataBlock]] = (
    DataBlock,
    CommentBlock,
    MediaBlock,
    XRDBlock,
    CycleBlock,
    NMRBlock,
    MassSpecBlock,
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
    "MassSpecBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
