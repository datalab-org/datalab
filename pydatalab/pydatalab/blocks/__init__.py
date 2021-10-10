from typing import Dict, Sequence, Type

from pydatalab.blocks.blocks import (
    CommentBlock,
    DataBlock,
    ImageBlock,
    SynthesisBlock,
    XRDBlock,
)
from pydatalab.blocks.echem_block import CycleBlock

BLOCKS: Sequence[Type[DataBlock]] = (
    DataBlock,
    CommentBlock,
    ImageBlock,
    XRDBlock,
    CycleBlock,
    SynthesisBlock,
)

BLOCK_TYPES: Dict[str, Type[DataBlock]] = {block.blocktype: block for block in BLOCKS}
BLOCK_TYPES["test"] = DataBlock

__all__ = (
    "DataBlock",
    "CommentBlock",
    "ImageBlock",
    "XRDBlock",
    "SynthesisBlock",
    "CycleBlock",
    "BLOCK_TYPES",
    "BLOCKS",
)
