from pydatalab.apps.chat.blocks import ChatBlock
from pydatalab.apps.echem import CycleBlock
from pydatalab.apps.eis import EISBlock
from pydatalab.apps.ftir import FTIRBlock
from pydatalab.apps.nmr import NMRBlock
from pydatalab.apps.raman import RamanBlock
from pydatalab.apps.tga import MassSpecBlock
from pydatalab.apps.xrd import XRDBlock
from pydatalab.blocks.base import DataBlock
from pydatalab.blocks.common import CommentBlock, MediaBlock, NotSupportedBlock, TabularDataBlock

BLOCKS: list[type["DataBlock"]] = [
    CommentBlock,
    MediaBlock,
    XRDBlock,
    CycleBlock,
    RamanBlock,
    NMRBlock,
    NotSupportedBlock,
    MassSpecBlock,
    ChatBlock,
    EISBlock,
    TabularDataBlock,
    FTIRBlock,
]

BLOCK_TYPES: dict[str, type["DataBlock"]] = {block.blocktype: block for block in BLOCKS}


def load_block_plugins():
    """Search through any registered entrypoints at 'pydatalab.apps.plugins'
    and load them as DataBlock subclasses.
    """
    import pkg_resources

    block_plugins: dict[str, type[DataBlock]] = {}
    for entry_point in pkg_resources.iter_entry_points("pydatalab.apps.plugins"):
        block = entry_point.load()

        if not issubclass(block, DataBlock):
            raise ValueError(f"Plugin {block} must be a subclass of DataBlock")

        if block.blocktype in BLOCK_TYPES:
            raise ValueError(f"Block type {block.blocktype} is already defined")

        BLOCK_TYPES[block.blocktype] = block
        BLOCKS.append(block)
        block_plugins[block.blocktype] = block

    return block_plugins


__all__ = (
    "CommentBlock",
    "MediaBlock",
    "XRDBlock",
    "ChatBlock",
    "EISBlock",
    "CycleBlock",
    "NotSupportedBlock",
    "NMRBlock",
    "RamanBlock",
    "MassSpecBlock",
    "TabularDataBlock",
    "FTIRBlock",
    "BLOCK_TYPES",
    "BLOCKS",
    "load_block_plugins",
)
