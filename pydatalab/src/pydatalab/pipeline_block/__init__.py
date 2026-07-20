# Base block import has to go first to avoid circular deps
from pydatalab.pipeline_block.base import PipelineDataBlock
from pydatalab.pipeline_block.common import (
    CommentBlockPipeline,
    MediaBlock,
    NotSupportedBlockPipeline,
    TabularPipelineDataBlock,
)

PIPELINE_COMMON_BLOCKS: list[type[PipelineDataBlock]] = [
    CommentBlockPipeline,
    MediaBlock,
    NotSupportedBlockPipeline,
    TabularPipelineDataBlock,
]

__all__ = ("PIPELINE_COMMON_BLOCKS", "PipelineDataBlock")
