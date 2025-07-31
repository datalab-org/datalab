"""This module provides a convenience wrapper for loading all
'app' blocks, which may or may not be available.

"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # This import is required to prevent circular imports for application-specific blocks
    from pydatalab.blocks.base import DataBlock  # noqa

from pydatalab.blocks import COMMON_BLOCKS


def _check_error(e):
    if "circular" in str(e):
        raise ImportError(e) from e


def load_app_blocks():
    app_blocks: list[type["DataBlock"]] = []

    try:
        # A dummy block that is used to check that bad blocks do not break the import
        from pydatalab.apps._canary import CanaryBlock

        app_blocks.append(CanaryBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.chat import ChatBlock

        app_blocks.append(ChatBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.echem import CycleBlock

        app_blocks.append(CycleBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.eis import EISBlock

        app_blocks.append(EISBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.ftir import FTIRBlock

        app_blocks.append(FTIRBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.nmr import NMRBlock

        app_blocks.append(NMRBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.raman import RamanBlock

        app_blocks.append(RamanBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.tga import MassSpecBlock

        app_blocks.append(MassSpecBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.uvvis import UVVisBlock

        app_blocks.append(UVVisBlock)
    except ImportError as e:
        _check_error(e)

    try:
        from pydatalab.apps.xrd import XRDBlock

        app_blocks.append(XRDBlock)
    except ImportError as e:
        _check_error(e)

    return app_blocks


BLOCKS = COMMON_BLOCKS + load_app_blocks()
BLOCK_TYPES: dict[str, type["DataBlock"]] = {block.blocktype: block for block in BLOCKS}


def load_block_plugins():
    """Search through any registered entrypoints at 'pydatalab.apps.plugins'
    and load them as DataBlock subclasses.
    """
    from importlib.metadata import entry_points

    from pydatalab.blocks.base import DataBlock

    block_plugins: dict[str, type[DataBlock]] = {}
    for entry_point in entry_points(group="pydatalab.apps.plugins"):
        block = entry_point.load()

        if not issubclass(block, DataBlock):
            raise ValueError(f"Plugin {block} must be a subclass of DataBlock")

        block_plugins[block.blocktype] = block

        if block.blocktype not in BLOCK_TYPES:
            BLOCK_TYPES[block.blocktype] = block
            BLOCKS.append(block)

    return block_plugins


load_block_plugins()
