# Base block import has to go first to avoid circular deps
from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.common import CommentBlock, MediaBlock, NotSupportedBlock, TabularDataBlock

COMMON_BLOCKS: list[type[DataBlock]] = [
    CommentBlock,
    MediaBlock,
    NotSupportedBlock,
    TabularDataBlock,
]

__all__ = ("COMMON_BLOCKS", "DataBlock")
