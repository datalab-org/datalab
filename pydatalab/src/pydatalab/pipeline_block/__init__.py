# Base block import has to go first to avoid circular deps
from pydatalab.pipeline_block.base import DataBlockDefaults
from pydatalab.pipeline_block.common import TABULAR_DATABLOCK

PIPELINE_COMMON_BLOCKS: list[dict] = [
    TABULAR_DATABLOCK,
]

__all__ = ("PIPELINE_COMMON_BLOCKS", "DataBlockDefaults")
