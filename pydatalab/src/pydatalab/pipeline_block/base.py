from typing import Any

from pydatalab import __version__
from pydatalab.models.blocks import DataBlockResponse
from pydatalab.models.utils import BaseModel

__all__ = ("DataBlockDefaults",)


class DataBlockDefaults(BaseModel):
    blocktype: str = "DataBlock"
    """Name of the datablock"""

    name: str = "base"
    """The human-readable block name specifying which technique
    or file format it pertains to.
    """
    description: str = "Generic pipeline Block"
    """A longer description outlining the purpose and capability
    of the block."""

    accepted_file_extensions: tuple[str, ...] | None = ()
    """A list of file extensions that the block will attempt to read."""

    defaults: dict[str, Any] = {}
    """Any default values that should be set if they are not
    supplied during block init.
    """

    multi_file: bool = False
    """Whether this block can accept multiple files as input."""

    block_db_model: type[DataBlockResponse] = DataBlockResponse
    """The DataBlockResponse model"""

    version: str = __version__
    """The implementation version of this particular block."""
