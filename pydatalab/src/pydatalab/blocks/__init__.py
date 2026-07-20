# Base block import has to go first to avoid circular deps
from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.common import (
    CommentBlock,
    LegacyMediaBlock,
    NotSupportedBlock,
    TabularDataBlock,
)

COMMON_BLOCKS: list[type[DataBlock]] = [
    CommentBlock,
    LegacyMediaBlock,
    NotSupportedBlock,
    TabularDataBlock,
]

__all__ = ("COMMON_BLOCKS", "DataBlock")
