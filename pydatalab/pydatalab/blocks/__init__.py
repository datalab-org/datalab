from typing import Dict, Sequence, Type

from pydatalab.blocks.blocks import (
    CommentBlock,
    DataBlock,
    ImageBlock,
    NotSupportedBlock,
    XRDBlock,
)
from pydatalab.blocks.echem_block import CycleBlock

BLOCKS: Sequence[Type[DataBlock]] = (
    DataBlock,
    CommentBlock,
    ImageBlock,
    XRDBlock,
    CycleBlock,
    NotSupportedBlock,
)

BLOCK_TYPES: Dict[str, Type[DataBlock]] = {block.blocktype: block for block in BLOCKS}
BLOCK_TYPES["test"] = DataBlock

__all__ = (
    "DataBlock",
    "CommentBlock",
    "ImageBlock",
    "XRDBlock",
    "CycleBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
