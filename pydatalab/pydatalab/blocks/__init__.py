from typing import Dict, Sequence, Type

from pydatalab.blocks.blocks import (
    ChatBlock,
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
    NotSupportedBlock,
    ChatBlock,
)

BLOCK_TYPES: Dict[str, Type[DataBlock]] = {block.blocktype: block for block in BLOCKS}
BLOCK_TYPES["test"] = DataBlock

__all__ = (
    "DataBlock",
    "CommentBlock",
    "MediaBlock",
    "XRDBlock",
    "ChatBlock",
    "CycleBlock",
    "NMRBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
